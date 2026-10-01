"""Authenticated plugin routes. No hooks, events, approval or core modifications."""
import io
import re
import uuid
from django.http import FileResponse
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from .contract import CAMERAS, PARAMETERS, InputRefusal, VERSION, parse_fps
from .core import run_assessment, verify_assessment, read_json, compare_snapshots, export_assessment
from .inventree_adapter import snapshot_for, state_root
from .errors import ReviewFailure, diagnostic, storage_failure
from .verification import verify, compatibility_info
from .assurance import host_requirement

class ReviewPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.has_perm('part.view_part'))

class Base(APIView):
    permission_classes = [ReviewPermission]

    def handle_exception(self, exc):
        if isinstance(exc, ReviewFailure):
            diagnostic(exc.code, category=exc.category)
            return Response({'state': exc.category, 'category': exc.category, 'code': exc.code, 'message': str(exc)}, status=exc.status)
        if isinstance(exc, OSError):
            return self.handle_exception(storage_failure(exc))
        if isinstance(exc, (ValueError, TypeError, KeyError)):
            diagnostic('UNEXPECTED_SERVER_FIELDS', exception=type(exc).__name__)
            return Response({'state': 'PROCESS_FAILURE', 'category': 'PROCESS_FAILURE', 'code': 'SERVER_FIELDS',
                             'message': 'The server could not process its configured record'}, status=500)
        return super().handle_exception(exc)

def request_int(value):
    try:
        if isinstance(value, bool): raise ValueError()
        return int(value)
    except (ValueError, TypeError):
        raise InputRefusal('REQUEST_FIELDS', 'A mapped part identifier is required')

def folder_for(identifier):
    if not re.fullmatch('[0-9a-f]{32}', identifier): raise InputRefusal('ASSESSMENT_ID', 'Invalid assessment identity')
    folder = state_root() / identifier / 'assessment'
    if not folder.is_dir(): raise InputRefusal('ASSESSMENT_MISSING', 'Assessment not available')
    verify_assessment(folder)
    return folder

def get_summary(folder):
    s = read_json(folder / 'summary.json')
    s['manifest_sha256'] = verify_assessment(folder)
    s['verification_compatibility'] = compatibility_info(read_json(folder / 'snapshot.json')['integration_version'])
    s['snapshot'] = read_json(folder / 'snapshot.json')
    s['mapping_trace'] = read_json(folder / 'mapping_trace.json')
    trace = folder / 'outputs/analyze/materialization_trace.json'
    s['source_trace'] = read_json(trace) if trace.exists() else {}
    return s

class Options(Base):
    def get(self, request):
        from company.models import ManufacturerPart
        from part.models import Part
        options = []
        for mp in ManufacturerPart.objects.select_related('manufacturer', 'part').filter(MPN__in=[v['mpn'] for v in CAMERAS.values()]):
            try:
                snap = snapshot_for(request_int(request.query_params.get('current')), mp.part_id)
                mode = snap['parameters']['isp_enabled'].get('raw_value')
                options.append({'part_id': mp.part_id, 'name': mp.part.name, 'mpn': mp.MPN, 'manufacturer': mp.manufacturer.name, 'isp_enabled': mode})
            except InputRefusal:
                continue
        return Response({'options': options, 'current_part': request_int(request.query_params.get('current')), 'version': VERSION, 'notice': 'Real source-backed model identities; synthetic installation only.'})

class Assessments(Base):
    def post(self, request):
        allowed = {'current_part', 'substitute_part', 'fast_required_fps'}
        if set(request.data) != allowed: raise InputRefusal('REQUEST_FIELDS', 'Exactly current_part, substitute_part and fast_required_fps are required')
        snapshot = snapshot_for(request_int(request.data['current_part']), request_int(request.data['substitute_part']), request.data['fast_required_fps'])
        result = run_assessment(snapshot, state_root())
        return Response(get_summary(folder_for(result['assessment_id'])), status=201)

    def get(self, request):
        current = request_int(request.query_params.get('current'))
        records = []
        for p in state_root().glob('*/assessment/summary.json'):
            try:
                folder = folder_for(p.parent.parent.name); snap = read_json(folder / 'snapshot.json')
                if snap['current_part']['object_id'] == current:
                    s = read_json(p); records.append({k:s[k] for k in ['assessment_id','created_utc','engineering_status','camera_id']})
            except (ReviewFailure, OSError, ValueError, KeyError):
                diagnostic('HISTORY_EXCLUDED', assessment_id=p.parent.parent.name, reason='Unverified record excluded without trusting its claimed part')
        return Response(sorted(records, key=lambda x:x['created_utc'], reverse=True))

class Assessment(Base):
    def get(self, request, identifier): return Response(get_summary(folder_for(identifier)))

class Compare(Base):
    def get(self, request, identifier):
        folder = folder_for(identifier); old = read_json(folder / 'snapshot.json')
        fps = request.query_params.get('fast_required_fps', old['requirements']['fast_required_fps'])
        try:
            parse_fps(fps)
        except InputRefusal:
            return Response({'state': 'INVALID_COMPARISON_INPUT', 'category': 'INPUT_ERROR', 'code': 'INVALID_COMPARISON_INPUT',
                             'message': 'Comparison requires an ASCII integer FPS assumption from 1 to 1000'}, status=400)
        try:
            new = snapshot_for(old['current_part']['object_id'], old['substitute_part']['object_id'], fps)
        except InputRefusal as exc:
            return Response({'state':'COMPARISON_UNRESOLVED','message':str(exc),'code':exc.code})
        return Response(compare_snapshots(old, new))

class Export(Base):
    def get(self, request, identifier):
        folder = folder_for(identifier); stream = io.BytesIO(); export_assessment(folder, stream); stream.seek(0)
        return FileResponse(stream, as_attachment=True, filename='higgs-assessment-' + identifier + '.zip', content_type='application/zip')

class Mode(Base):
    def post(self, request):
        if not request.user.has_perm('part.change_part'):
            return Response({'message':'Part-change permission required'}, status=403)
        from django.contrib.contenttypes.models import ContentType
        from common.models import Parameter
        from part.models import Part
        if set(request.data) != {'part_id','isp_enabled'} or request.data['isp_enabled'] not in ['false','true','unknown']:
            raise InputRefusal('MODE_INPUT', 'Only an explicit false/true/unknown demonstration declaration is supported')
        rows = Parameter.objects.filter(model_type=ContentType.objects.get_for_model(Part), model_id=request_int(request.data['part_id']), template__name=PARAMETERS['isp_enabled'])
        if rows.count() != 1: raise InputRefusal('MODE_BINDING', 'Missing or ambiguous declared ISP parameter')
        row = rows.get(); before = row.data; row.data = request.data['isp_enabled']; row.updated_by = request.user; row.save()
        return Response({'part_id':row.model_id,'before':before,'after':row.data,'meaning':'Synthetic operating declaration changed; no camera hardware action'})


class Verification(Base):
    def post(self, request, identifier):
        if not {'level'} <= set(request.data) <= {'level','require_assurance'} or request.data['level'] not in ('engine', 'decision'):
            raise InputRefusal('VERIFY_LEVEL', 'An engine or decision level and optional recipient assurance are supported')
        folder = folder_for(identifier)
        out = state_root() / 'verification-runs' / uuid.uuid4().hex
        required, minimum = host_requirement(request.data.get('require_assurance'))
        result = verify(folder, out, request.data['level'], required, 'Operator policy plus optional non-lowering request')
        result['recipient_requirement']['operator_minimum'] = minimum
        status = 200 if result['assurance_level'] != 'NOT_VERIFIED' else (500 if result.get('category') in ('CONFIGURATION_ERROR','STORAGE_FAILURE','PROCESS_FAILURE') else 422)
        return Response(result, status=status)
