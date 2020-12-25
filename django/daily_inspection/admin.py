from django.contrib import admin
from plugin.admin import my_admin_site
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext_lazy as _

from django.contrib.admin import AdminSite
from django.views.decorators.cache import never_cache
from django.utils import timezone

from .models import (
    DailyInspection,
    )
    
from .forms import (
    DailyInspectionAdminForm,
)
# Register your models here.

class DailyInspectionAdmin(admin.ModelAdmin):
    list_display = ['inspection_content', "category","rectification_status",'owner','due_date','created','updated','location']
    list_editable = ["category","rectification_status",'owner','location']
    list_filter = ["category", "rectification_status",'owner','location']
    search_fields = ["category", 'inspection_content',"rectification_status",'owner','due_date','created','updated','location']
    list_display_links = ['inspection_content']
    ordering = ['-created']
    list_per_page = 10
    list_max_show_all = 80

    form = DailyInspectionAdminForm
    
    class Meta:
        model = DailyInspection

    class Media:
        css = {
            "all": ("css/model_admin.css", "css/inspection.css", )
        }
        js = ("js/jquery.min.js","js/model_admin.js",)
        

    def view_on_site(self, obj):
        url = reverse('dailyinspection_detail', kwargs={'pk': obj.pk})
        return url

    def save_model(self, request, obj, form, change):

        re = super(DailyInspectionAdmin,self).save_model(request, obj, form, change)
        if obj.rectification_status == 'completed':
            obj.completed_time = timezone.now()
            obj.save()
        return re

admin.site.register(DailyInspection, DailyInspectionAdmin)
