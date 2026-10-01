"""Explicit reads from InvenTree 1.5.6; no automatic evidence admission."""
import os
import platform
from pathlib import Path
from .contract import PARAMETERS, DEPENDENCY_SHA, InputRefusal, VERSION, software_identity
from .core import archive_path, digest

def snapshot_for(current_id, substitute_id, fast_fps='45'):
    from django.contrib.contenttypes.models import ContentType
    from common.models import Parameter
    from company.models import ManufacturerPart
    from part.models import Part
    from InvenTree.version import INVENTREE_SW_VERSION
    try:
        current, part = Part.objects.get(pk=current_id), Part.objects.get(pk=substitute_id)
    except Part.DoesNotExist:
        raise InputRefusal('PART_MISSING', 'Part identity is unavailable')
    mp = list(ManufacturerPart.objects.filter(part_id=part.pk).select_related('manufacturer'))
    if len(mp) != 1:
        raise InputRefusal('MANUFACTURER_BINDING', 'Exactly one explicitly bound manufacturer part is required')
    rows, audit = {}, {'part_updated': str(getattr(part, 'updated', '')), 'parameter_updated': {}}
    ct = ContentType.objects.get_for_model(Part)
    for logical, name in PARAMETERS.items():
        params = list(Parameter.objects.filter(model_type=ct, model_id=part.pk, template__name=name).select_related('template'))
        if len(params) != 1:
            rows[logical] = {'missing': True, 'parameter_name': name, 'part_id': part.pk}
        else:
            param = params[0]
            rows[logical] = {'object_type': 'common.Parameter', 'object_id': param.pk, 'part_id': part.pk,
                'parameter_name': name, 'template_id': param.template_id, 'units': param.template.units,
                'raw_value': param.data}
            audit['parameter_updated'][str(param.pk)] = str(param.updated)
    artifact = archive_path()
    runtime_identity = digest(artifact.read_bytes()) if artifact.is_file() else 'MISSING'
    return {'schema': 'higgs-inventree-consumed-v1', 'instance_id': os.environ.get('HIGGS_INSTANCE_ID', 'unconfigured'),
        'inventree_version': INVENTREE_SW_VERSION, 'integration_version': VERSION,
        'current_part': {'object_id': current.pk, 'name': current.name, 'role': 'fictional incumbent/context; retained synthetic legacy baseline'},
        'substitute_part': {'object_id': part.pk, 'name': part.name},
        'manufacturer_part': {'object_id': mp[0].pk, 'manufacturer_id': mp[0].manufacturer_id, 'manufacturer': mp[0].manufacturer.name, 'mpn': mp[0].MPN},
        'parameters': rows, 'requirements': {'fast_required_fps': str(fast_fps), 'classification': 'synthetic_user_requirement'},
        'runtime': {'pinned_original_archive_sha256': DEPENDENCY_SHA, 'configured_runtime_sha256': runtime_identity, 'python': platform.python_version(), 'integration_source_sha256': software_identity()},
        'audit': audit}

def state_root():
    value = os.environ.get('HIGGS_STATE_ROOT')
    if not value:
        raise InputRefusal('CONFIGURATION', 'Administrator must configure a separate HIGGS_STATE_ROOT')
    return Path(value).resolve()
