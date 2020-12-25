import time, datetime
from datetime import timedelta
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.db.models import Q

import calendar

from .models import DailyInspection, PI, WHPI, RTPI
from equipments.models import EquipmentInspection, SprayPumpRoomInspection, SprayWarehouseInspection

def get_last_times(in_year):
    if not in_year:
        year = timezone.now().year
    else:
        year = in_year
    times = [[i, year] for i in range(1,13)]
    times = times + [["",year],]
    return times

def get_model_queryset(model, category,rectification_status, year,month):

    q = None

    if year and month:
        q = q & Q(created__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(created__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(created__startswith="{0}-".format(year)) if q else Q(created__startswith="{0}-".format(year))
    if category:
        q = q & Q(category__exact=category) if q else Q(category__exact=category)
    if rectification_status:
        q = q & Q(rectification_status__exact=rectification_status) if q else Q(rectification_status__exact=rectification_status)

    qs = model.objects.filter(q) if q else model.objects.all()

    return qs

def get_model_url(category,rectification_status, year,month):
    url = reverse("dailyinspection_list", kwargs={}) 
    q = None
    if category[0]:
        q = "?category={0}".format(category[0])
    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if rectification_status:
        q = "{0}&rectification_status={1}".format(q,rectification_status) if q else\
            "?rectification_status={0}".format(rectification_status)

    return "{0}{1}".format(url, q)

def get_daily_inspection_rows():
    return DailyInspection.daily_insepction_category + (('', _('Total')),)


def get_daily_inspection_total(in_year):
    return [[get_model_queryset(DailyInspection, category[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_daily_inspection_rows()]

def get_daily_inspection_uncompleted(in_year):
    return [[get_model_queryset(DailyInspection, category[0],"uncompleted",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_daily_inspection_rows()]

    return [[DailyInspection.objects.filter(category=category[0], rectification_status="uncompleted",created__startswith="{0}-{1:0>2d}-".format(year,month)).count() if category[0] else\
            DailyInspection.objects.filter(rectification_status="uncompleted",created__startswith="{0}-{1:0>2d}-".format(year,month)).count()\
                for month, year in get_last_times()] \
                    for category in get_daily_inspection_rows()]             

def get_daily_inspection_total_url(in_year):
    return [[get_model_url(category,'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_daily_inspection_rows()]   

    url = reverse("dailyinspection_list", kwargs={}) 
    return [["{0}?category={1}&start={2}-{3}-01&end={2}-{3}-{4}".format(url, category[0],year,month,calendar.monthrange(year, month)[1]) if category[0] else\
            "{0}?start={1}-{2}-01&end={1}-{2}-{3}".format(url, year,month,calendar.monthrange(year, month)[1])\
                for month, year in get_last_times()] \
                    for category in get_daily_inspection_rows()]    

def get_daily_inspection_completed(in_year):
    return [[get_model_queryset(DailyInspection, category[0],"completed",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_daily_inspection_rows()]

def get_daily_inspection_uncompleted_url(in_year):

    return [[get_model_url(category,'uncompleted',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_daily_inspection_rows()]   

    url = reverse("dailyinspection_list", kwargs={}) 
    return [["%s?q=&category=%s&rectification_status=uncompleted&start=%s-%s-01&end=%s-%s-%s" % (url, category[0],year,month,year,month,calendar.monthrange(year, month)[1]) if category[0] else\
            "%s?q=&rectification_status=uncompleted&start=%s-%s-01&end=%s-%s-%s" % (url,year,month,year,month,calendar.monthrange(year, month)[1]) \
                for month, year in get_last_times()] \
                    for category in get_daily_inspection_rows()]    

def get_daily_inspection_efficiency(in_year):
    efficiency_array = get_daily_inspection_completed(in_year)

    for i, category in enumerate(get_daily_inspection_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_model_queryset(DailyInspection, category[0],"completed",year,month)
            # completed_qs = DailyInspection.objects.filter(category=category[0], rectification_status="completed", created__startswith="{0}-{1:0>2d}-".format(year,month)) if category[0] else\
            #         DailyInspection.objects.filter(rectification_status="completed", created__startswith="{0}-{1:0>2d}-".format(year,month))
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

# >>>>>>>>>>>>>>>
def get_pi_rows():
    # return (('WH PI/NM', _('WH PI/NM')),) + (('RT PI/NM', _('RT PI/NM')),) + (('', _('Total')),)
    return (('WHPI', _('WH PI/NM')),) + (('RTPI', _('RT PI/NM')),) #+ (('', _('Total')),)

def get_pi_model_queryset(category,rectification_status, year,month):

    model = PI
    if category == "WHPI":
        model = WHPI
    elif category == "RTPI":
        model = RTPI

    q = None

    if year and month:
        q = q & Q(created__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(created__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(created__startswith="{0}-".format(year)) if q else Q(created__startswith="{0}-".format(year))

    if rectification_status:
        q = q & Q(rectification_status__exact=rectification_status) if q else Q(rectification_status__exact=rectification_status)

    qs = model.objects.filter(q) if q else model.objects.all()

    return qs

def get_whpi_total(in_year):
    return [[get_pi_model_queryset(category[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_pi_rows()]

def get_whpi_uncompleted(in_year):
    return [[get_pi_model_queryset(category[0],"uncompleted",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_pi_rows()]

def get_whpi_efficiency(in_year):
    efficiency_array = get_whpi_uncompleted(in_year)

    for i, category in enumerate(get_pi_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_pi_model_queryset(category[0],"completed",year,month)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_pi_model_url(category,rectification_status, year,month):
    url = reverse("pi_list", kwargs={}) 
    if category == "WHPI":
        url = reverse("whpi_list", kwargs={}) 
    elif category == "RTPI":
        url = reverse("rtpi_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if rectification_status:
        q = "{0}&rectification_status={1}".format(q,rectification_status) if q else\
            "?rectification_status={0}".format(rectification_status)

    return "{0}{1}".format(url, q)

def get_pi_total_url(in_year):
    return [[get_pi_model_url(category[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_pi_rows()]       

def get_pi_uncompleted_url(in_year):

    return [[get_pi_model_url(category[0],'uncompleted',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_pi_rows()] 

# >>>>>>>>>>>>>>>>>>>>>>>>>>
def get_spray_rows():
    return (('SprayPumpRoomInspection', _('Spray Pump Room')),) + (('SprayWarehouseInspection', _('Spray Warehouse')),) #

def get_spary_model_queryset(model_name,rectification_status, year,month):

    model = None
    from equipments import models
    model = getattr(models,model_name)()

    q = None

    if year and month:
        q = q & Q(year=year,month="{0:0>2d}".format(month)) if q else Q(year=year,month="{0:0>2d}".format(month))
    else:
        q = q & Q(year=year) if q else Q(year=year)

    if rectification_status:
        q = q & Q(rectification_status__exact=rectification_status) if q else Q(rectification_status__exact=rectification_status)

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_spray_total(in_year):
    return [[get_spary_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_spray_rows()]

def get_spray_uncompleted(in_year):
    return [[get_spary_model_queryset(model_name[0],"uncompleted",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_spray_rows()]

def get_spray_efficiency(in_year):
    efficiency_array = get_spray_uncompleted(in_year)

    for i, model_name in enumerate(get_spray_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_spary_model_queryset(model_name[0],"completed",year,month)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_spary_model_url(category,rectification_status, year,month):
    url = None
    if category == "SprayPumpRoomInspection":
        url = reverse("spraypumproominspection_list_display", kwargs={}) 
    elif category == "SprayWarehouseInspection":
        url = reverse("spraywarehouseinspection_list_display", kwargs={}) 

    q = None

    if year:
        q = "?year={0}".format(year) 
    else:
        q = ""   

    return "{0}{1}".format(url, q)

def get_spray_total_url(in_year):
    return [[get_spary_model_url(category[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_spray_rows()]       

def get_spray_uncompleted_url(in_year):

    return [[get_spary_model_url(category[0],'uncompleted',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_spray_rows()]                     

# >>>>>>>>>>>>>>>
def get_hydrant_rows():
    return (('ExtinguisherInspection', _('extinguisher')),) + (('HydrantInspection', _('hydrant')),) #+ (('', _('Total')),)

def get_hydrant_model_queryset(model_name,check_result, year,month, is_efficiency=False):

    model = None
    from inspection import models
    model = getattr(models,model_name)()

    q = None

    if year and month:
        q = q & Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(check_date__startswith="{0}-".format(year)) if q else Q(check_date__startswith="{0}-".format(year))

    if check_result:
        q = q & Q(check_result__exact=check_result) if q else Q(check_result__exact=check_result)

    if is_efficiency:
        q = q & Q(completed_time__gte="{0}-01-01".format(year)) if q else Q(completed_time__gte="{0}-01-01".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_hydrant_total(in_year):
    return [[get_hydrant_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_hydrant_rows()]

def get_hydrant_uncompleted(in_year):
    return [[get_hydrant_model_queryset(model_name[0],"breakdown",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_hydrant_rows()]

def get_hydrant_efficiency(in_year):
    efficiency_array = get_hydrant_uncompleted(in_year)

    for i, model_name in enumerate(get_hydrant_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_hydrant_model_queryset(model_name[0],"normal",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_hydrant_model_url(model_name,check_result, year,month):
    url = None
    if model_name == "ExtinguisherInspection":
        url = reverse("extinguisherinspection_list", kwargs={}) 
    elif model_name == "HydrantInspection":
        url = reverse("hydrantinspection_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if check_result:
        q = "{0}&check_result={1}".format(q,check_result) if q else\
            "?check_result={0}".format(check_result)

    return "{0}{1}".format(url, q)

def get_hydrant_total_url(in_year):
    return [[get_hydrant_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_hydrant_rows()]       

def get_hydrant_uncompleted_url(in_year):

    return [[get_hydrant_model_url(model_name[0],'breakdown',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_hydrant_rows()] 


# >>>>>>>>>>>>>>>
from equipments.models import EquipmentType, Equipment, EquipmentInspection
def get_other_equipment_rows():
    return [(instance, instance.name ) for instance in EquipmentType.objects.all()] + [('', _('Total')),]

def get_other_equipment_model_queryset(category,check_result, year,month, is_efficiency=False):

    q = None
    if category:
        q = Q(equipment__type__id__exact=category.id) 

    if year and month:
        q = q & Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(check_date__startswith="{0}-".format(year)) if q else Q(check_date__startswith="{0}-".format(year))

    if check_result:
        q = q & Q(use_condition__exact=check_result) if q else Q(use_condition__exact=check_result)

    if is_efficiency:
        q = q & Q(completed_time__gte="{0}-01-01".format(year)) if q else Q(completed_time__gte="{0}-01-01".format(year))

    qs = EquipmentInspection.objects.filter(q) if q else EquipmentInspection.objects.all()

    return qs

def get_other_equipment_total(in_year):
    return [[get_other_equipment_model_queryset(category[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_other_equipment_rows()]

def get_other_equipment_uncompleted(in_year):
    return [[get_other_equipment_model_queryset(category[0],"breakdown",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for category in get_other_equipment_rows()]

def get_other_equipment_efficiency(in_year):
    efficiency_array = get_other_equipment_uncompleted(in_year)

    for i, category in enumerate(get_other_equipment_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_other_equipment_model_queryset(category[0],"normal",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_other_equipment_model_url(category,check_result, year,month):
    
    url = reverse("equipmentinsepction_list", kwargs={}) 
    q = None
    if category:
        q = "?category_id={0}".format(category.id)

    if year and month:
        q = "{0}&date_of_inspection_start={1}-{2}-01&date_of_inspection_end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?date_of_inspection_start={0}-{1}-01&date_of_inspection_end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&date_of_inspection_start={1}-01-01&date_of_inspection_end={1}-12-31".format(q,year) if q else\
            "?date_of_inspection_start={0}-01-01&date_of_inspection_end={0}-12-31".format(year)        
    if check_result:
        q = "{0}&use_condition={1}".format(q,check_result) if q else\
            "?use_condition={0}".format(check_result)

    return "{0}{1}".format(url, q)

def get_other_equipment_total_url(in_year):
    return [[get_other_equipment_model_url(category[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_other_equipment_rows()]       

def get_other_equipment_uncompleted_url(in_year):

    return [[get_other_equipment_model_url(category[0],'breakdown',year,month) \
                for month, year in get_last_times(in_year)] \
                    for category in get_other_equipment_rows()] 


# >>>>>>>>>>>>>>> shelf inspection
def get_shelf_inspection_rows():
    return (('', _('Total')),)

def get_shelf_inspection_model_queryset(model_name,check_result, year,month, is_efficiency=False):

    model = None
    from inspection import models
    model = getattr(models,'shelf_inspection_record')()

    q = None

    if year and month:
        q = q & Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(check_date__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(check_date__startswith="{0}-".format(year)) if q else Q(check_date__startswith="{0}-".format(year))

    if check_result:
        q = q & Q(use_condition__exact=check_result) if q else Q(use_condition__exact=check_result)

    if is_efficiency:
        q = q & Q(completed_time__gte="{0}-01-01".format(year)) if q else Q(completed_time__gte="{0}-01-01".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_shelf_inspection_total(in_year):
    return [[get_shelf_inspection_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_shelf_inspection_rows()]

def get_shelf_inspection_uncompleted(in_year):
    return [[get_shelf_inspection_model_queryset(model_name[0],"breakdown",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_shelf_inspection_rows()]

def get_shelf_inspection_efficiency(in_year):
    efficiency_array = get_shelf_inspection_uncompleted(in_year)

    for i, model_name in enumerate(get_shelf_inspection_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_shelf_inspection_model_queryset(model_name[0],"normal",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_shelf_inspection_model_url(model_name,check_result, year,month):
    url = reverse("shelf_inspection_record_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if check_result:
        q = "{0}&check_result={1}".format(q,check_result) if q else\
            "?check_result={0}".format(check_result)

    return "{0}{1}".format(url, q)

def get_shelf_inspection_total_url(in_year):
    return [[get_shelf_inspection_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_shelf_inspection_rows()]       

def get_shelf_inspection_uncompleted_url(in_year):

    return [[get_shelf_inspection_model_url(model_name[0],'breakdown',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_shelf_inspection_rows()] 

# >>>>>>>>>>>>>>> vehicle inspection
def get_vehicle_inspection_rows():
    return (('', _('Total')),)

def get_vehicle_inspection_model_queryset(model_name,check_result, year,month, is_efficiency=False):

    model = None
    from outsourcing import models
    model = getattr(models,'VehicleInspection')()

    q = None

    if year and month:
        q = q & Q(created__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(created__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(created__startswith="{0}-".format(year)) if q else Q(created__startswith="{0}-".format(year))

    if check_result:
        q = q & Q(rectification_qualified__exact=check_result) if q else Q(rectification_qualified__exact=check_result)

    if is_efficiency:
        q = q & Q(completed_time__gte="{0}-01-01".format(year)) if q else Q(completed_time__gte="{0}-01-01".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_vehicle_inspection_total(in_year):
    return [[get_vehicle_inspection_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_vehicle_inspection_rows()]

def get_vehicle_inspection_uncompleted(in_year):
    return [[get_vehicle_inspection_model_queryset(model_name[0],"no",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_vehicle_inspection_rows()]

def get_vehicle_inspection_efficiency(in_year):
    efficiency_array = get_vehicle_inspection_uncompleted(in_year)

    for i, model_name in enumerate(get_vehicle_inspection_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_vehicle_inspection_model_queryset(model_name[0],"yes",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_vehicle_inspection_model_url(model_name,check_result, year,month):
    url = reverse("vehicle_inspection_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if check_result:
        q = "{0}&rectification_qualified={1}".format(q,check_result) if q else\
            "?rectification_qualified={0}".format(check_result)

    return "{0}{1}".format(url, q)

def get_vehicle_inspection_total_url(in_year):
    return [[get_vehicle_inspection_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_vehicle_inspection_rows()]       

def get_vehicle_inspection_uncompleted_url(in_year):

    return [[get_vehicle_inspection_model_url(model_name[0],'no',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_vehicle_inspection_rows()] 


# >>>>>>>>>>>>>>> forklift repair
def get_forklift_repair_rows():
    return (('', _('Total')),)

def get_forklift_repair_model_queryset(model_name,check_result, year,month, is_efficiency=False):

    model = None
    from outsourcing import models
    model = getattr(models,'ForkliftRepair')()

    q = None

    if year and month:
        q = q & Q(created__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(created__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(created__startswith="{0}-".format(year)) if q else Q(created__startswith="{0}-".format(year))

    if check_result:
        q = q & Q(repaired__exact=check_result) if q else Q(repaired__exact=check_result)

    if is_efficiency:
        q = q & Q(repaire_date__gte="{0}-01-01".format(year)) if q else Q(repaire_date__gte="{0}-01-01".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_forklift_repair_total(in_year):
    return [[get_forklift_repair_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_repair_rows()]

def get_forklift_repair_uncompleted(in_year):
    return [[get_forklift_repair_model_queryset(model_name[0],"no",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_repair_rows()]

def get_forklift_repair_efficiency(in_year):
    efficiency_array = get_forklift_repair_uncompleted(in_year)

    for i, model_name in enumerate(get_forklift_repair_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_forklift_repair_model_queryset(model_name[0],"yes",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + instance.time_consuming()
            efficiency_array[i][j]= time_consumings / completed_qs.count() if completed_qs.count() else '-'
    return efficiency_array

def get_forklift_repair_model_url(model_name,check_result, year,month):
    url = reverse("forklift_repair_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if check_result:
        q = "{0}&repaired={1}".format(q,check_result) if q else\
            "?repaired={0}".format(check_result)

    return "{0}{1}".format(url, q)

def get_forklift_repair_total_url(in_year):
    return [[get_forklift_repair_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_repair_rows()]       

def get_forklift_repair_uncompleted_url(in_year):

    return [[get_forklift_repair_model_url(model_name[0],'no',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_repair_rows()] 


# >>>>>>>>>>>>>>> forklift maint
def get_forklift_maint_rows():
    return (('', _('Total')),)

def get_forklift_maint_model_queryset(model_name,check_result, year,month):

    model = None
    from outsourcing import models
    model = getattr(models,'ForkliftMaint')()

    q = None

    if year and month:
        q = q & Q(created__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(created__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(created__startswith="{0}-".format(year)) if q else Q(created__startswith="{0}-".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_forklift_maint_total(in_year):
    return [[get_forklift_maint_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_maint_rows()]

def get_forklift_maint_uncompleted(in_year):
    return [[get_forklift_maint_model_queryset(model_name[0],"-",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_maint_rows()]

def get_forklift_maint_cost(in_year):
    efficiency_array = get_forklift_repair_uncompleted(in_year)

    for i, model_name in enumerate(get_forklift_maint_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            costs = 0
            completed_qs = get_forklift_maint_model_queryset(model_name[0],"-",year,month)
            for instance in completed_qs:
                costs = costs + instance.expense
            # efficiency_array[i][j]= costs / completed_qs.count() if completed_qs.count() else '-'
            efficiency_array[i][j]= costs if completed_qs.count() else '-'
    return efficiency_array

def get_forklift_maint_model_url(model_name,check_result, year,month):
    url = reverse("forklift_maint_list", kwargs={}) 

    q = None

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        

    return "{0}{1}".format(url, q)

def get_forklift_maint_total_url(in_year):
    return [[get_forklift_maint_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_maint_rows()]       

def get_forklift_maint_uncompleted_url(in_year):

    return [[get_forklift_maint_model_url(model_name[0],'-',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_forklift_maint_rows()] 


# >>>>>>>>>>>>>>> annual training plan
def get_annual_training_plan_rows():
    return (('warehouse',_('Storage Security')), ('transportation',_('Transport Security')), ) #('', _('Total')),)

def get_annual_training_plan_model_queryset(model_name,check_result, year,month, is_efficiency=False):

    model = None
    from trainings import models
    model = getattr(models,'AnnualTraningPlan')()

    q = None
    if model_name:
        q = Q(training_course__training_class__exact=model_name)

    if year and month:
        q = q & Q(planned_date__startswith="{0}-{1:0>2d}-".format(year,month)) if q else Q(planned_date__startswith="{0}-{1:0>2d}-".format(year,month))
    else:
        q = q & Q(planned_date__startswith="{0}-".format(year)) if q else Q(planned_date__startswith="{0}-".format(year))

    if check_result == 'no':
        q = q & ~Q(actual_date__startswith="{0}-".format(year)) if q else ~Q(actual_date__startswith="{0}-".format(year))
    elif check_result == 'yes':
        q = q & Q(actual_date__startswith="{0}-".format(year)) if q else Q(actual_date__startswith="{0}-".format(year))

    qs = model.__class__.objects.filter(q) if q else model.objects.all()

    return qs

def get_annual_training_plan_total(in_year):
    return [[get_annual_training_plan_model_queryset(model_name[0],"",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_annual_training_plan_rows()]

def get_annual_training_plan_uncompleted(in_year):
    return [[get_annual_training_plan_model_queryset(model_name[0],"no",year,month).count()\
                for month, year in get_last_times(in_year)] \
                    for model_name in get_annual_training_plan_rows()]

def get_annual_training_plan_ratio(in_year):
    efficiency_array = get_annual_training_plan_uncompleted(in_year)    

    for i, model_name in enumerate(get_annual_training_plan_rows()):
        for j, [month, year] in enumerate(get_last_times(in_year)):            
            time_consumings = 0
            completed_qs = get_annual_training_plan_model_queryset(model_name[0],"yes",year,month,is_efficiency=True)
            total_qs = get_annual_training_plan_model_queryset(model_name[0],"-",year,month,is_efficiency=True)
            for instance in completed_qs:
                time_consumings = time_consumings + 1 if instance.on_schedule() else 0
            efficiency_array[i][j]= "{0:.1%}".format(time_consumings*1.0 / total_qs.count()) if total_qs.count() else '-'
    return efficiency_array

def get_annual_training_plan_model_url(model_name,check_result, year,month):
    url = reverse("annualtrainingplan_list", kwargs={}) 

    q = None
    if model_name:
        q = "?class={0}".format(model_name)

    if year and month:
        q = "{0}&start={1}-{2}-01&end={1}-{2}-{3}".format(q,year,month,calendar.monthrange(year, month)[1]) if q else\
            "?start={0}-{1}-01&end={0}-{1}-{2}".format(year,month,calendar.monthrange(year, month)[1])
    else:
        q = "{0}&start={1}-01-01&end={1}-12-31".format(q,year) if q else\
            "?start={0}-01-01&end={0}-12-31".format(year)        
    if 'no' == check_result:
        q = "{0}&uncompleted=True".format(q) if q else\
            "?uncompleted=True"

    return "{0}{1}".format(url, q)

def get_annual_training_plan_total_url(in_year):
    return [[get_annual_training_plan_model_url(model_name[0],'',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_annual_training_plan_rows()]       

def get_annual_training_plan_uncompleted_url(in_year):

    return [[get_annual_training_plan_model_url(model_name[0],'no',year,month) \
                for month, year in get_last_times(in_year)] \
                    for model_name in get_annual_training_plan_rows()] 
