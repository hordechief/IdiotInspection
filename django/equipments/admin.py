from django.contrib import admin

from .models import (
    Equipment, 
    EquipmentType,
    EquipmentInspection,
    )

# Register your models here.
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    #list_editable = ["name"]
    list_filter = [ "name"]

    view_on_site = False

    class Meta:
        model = EquipmentType

class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["name","type"]
    list_editable = [ "type"]
    list_filter = [ "type"]

    view_on_site = False

    class Meta:
        model = Equipment

class EquipmentInspectionAdmin(admin.ModelAdmin):
    list_display = ["equipment","use_condition","inspector","check_date","updated","owner","due_date","completed_time"]
    list_editable = ["use_condition","owner","due_date"]
    list_filter = ["equipment","use_condition","inspector","check_date"]
    #form = EquipmentInspectionForm

    view_on_site = False

    class Meta:
        model = EquipmentInspection

    class Media:
        css = {
            "all": ("css/model_admin.css","css/equipment.css")
        }
        js = ("js/jquery.min.js","js/model_admin.js",)

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(EquipmentType, EquipmentTypeAdmin)
admin.site.register(EquipmentInspection, EquipmentInspectionAdmin)
