from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import AdminSite
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.sites.models import Site
from django.conf import settings

# extra_app_list
# admin_site
# base_data

# Register your models here.

class MyAdminSite(AdminSite):
    site_header = 'SINOTRANS'
    site_title = "SINOTRANS"
    #site_url = None
    index_title = _("SINOTRANS Management")
    """        
    index_template
    app_index_template
    empty_value_display
    login_template
    login_form
    logout_template
    password_change_template
    password_change_done_template
    """

    @never_cache    
    def index(self, request, extra_context=None):
        extra_app_list = [
            'warehouseio', 
            'authwrapper', 
            'auth',
            'contenttypes',
            'sessions',
            'sites',
        ]
        
        extra_context = {
            'extra_app_list' : extra_app_list,
            'admin_site' : 'sino',
            'base_data' : [
                'Hydrant',
                'Extinguisher',
                'shelf',
                'ShelfImport',
                'Equipment',
                'EquipmentType',
                'Forklift',
                'Vehicle',
                'Driver',
                'Article',
                'Banner',
                'AnnualPlanCategory',
                'TrainingCourse'
            ]
        }

        return super(MyAdminSite, self).index(request, extra_context)

    def app_index(self, request, app_label, extra_context=None):        
        extra_app_list = [
            'warehouseio', 
            'authwrapper', 
            'auth',
            'contenttypes',
            'sessions',
            'sites',
        ]
        
        extra_context = {
            'extra_app_list' : extra_app_list,
            'admin_site' : 'sino',
            'base_data' : [
                'Hydrant',
                'Extinguisher',
                'shelf',
                'ShelfImport',
                'Equipment',
                'EquipmentType',
                'Forklift',
                'Vehicle',
                'Driver',
                'Article',
                'Banner',
                'AnnualPlanCategory',
                'TrainingCourse'
            ]
        }

        return super(MyAdminSite, self).app_index(request, app_label, extra_context)
        
my_admin_site = MyAdminSite(name='sinotrans')


class SessionAdmin(admin.ModelAdmin):
    list_display = ["session_key","expire_date" ,"session_data", ]
    class Meta:
        model = Session

    list_per_page = 10
    list_max_show_all = 20

class SiteAdmin(admin.ModelAdmin):
    list_display = ["domain","name", ]
    class Meta:
        model = Site

    list_per_page = 10
    list_max_show_all = 20

my_admin_site.register(Session, SessionAdmin)        
my_admin_site.register(Site, SiteAdmin)   