from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class DailyInspectionConfig(AppConfig):
    name = 'daily_inspection'
    verbose_name = _("DailyInspection")
