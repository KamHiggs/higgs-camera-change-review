"""Supported InvenTree URL and user-interface extension points."""
from plugin import InvenTreePlugin
from plugin.mixins import UrlsMixin, UserInterfaceMixin

class HiggsCameraReview(UrlsMixin, UserInterfaceMixin, InvenTreePlugin):
    NAME = 'Higgs Camera Review'
    SLUG = 'higgs-camera-review'
    TITLE = 'Higgs Camera Review'
    DESCRIPTION = 'Evidence-aware advisory review in an explicitly synthetic installation'
    VERSION = '0.1.3'
    AUTHOR = 'Kamden Higgs'
    MIN_VERSION = '1.5.6'
    MAX_VERSION = '1.5.6'

    def setup_urls(self):
        from django.urls import path
        from .views import Options, Assessments, Assessment, Compare, Export, Mode, Verification
        return [path('options/', Options.as_view()), path('assessments/', Assessments.as_view()),
                path('assessments/<str:identifier>/', Assessment.as_view()),
                path('assessments/<str:identifier>/compare/', Compare.as_view()),
                path('assessments/<str:identifier>/export/', Export.as_view()), path('assessments/<str:identifier>/verify/', Verification.as_view()), path('mode/', Mode.as_view())]

    def get_ui_panels(self, request, context, **kwargs):
        if context.get('target_model') != 'part' or not request.user.has_perm('part.view_part'):
            return []
        return [{'key': 'higgs-camera-review', 'title': 'Higgs camera review', 'icon': 'ti:shield-check:outline',
                 'description': 'Real camera captures • synthetic installation • advisory only',
                 'source': self.plugin_static_file('panel.js:renderPanel')}]
