from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.base import View, TemplateResponseMixin, ContextMixin, TemplateView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.db import models
from django.forms import models as model_forms
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone
from django_filters import FilterSet, CharFilter, NumberFilter, BooleanFilter, MultipleChoiceFilter # MethodFilter, 
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from chartjs.views.lines import (JSONView, BaseLineChartView)
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import timedelta

from django.db.models.fields.related import (
    ForeignObjectRel, ManyToOneRel, OneToOneField,#add_lazy_relation,
)

from PIL import Image

import json
import time, datetime
import os

from plugin.var import month_choice
from plugin.mixins import StaffRequiredMixin, TableListViewMixin, TableDetailViewMixin, UpdateViewMixin, CreateViewMixin

# Create your views here.
from .models import (
    DailyInspection, 
    DailyInspectionLog,
    image_upload_to_dailyinspection,
    )

from .forms import (
    DailyInspectionForm, 
    InspectionFilterForm, 
    )

# Create your views here.

def gen_qrcode(link):
    import qrcode
    qr=qrcode.QRCode(
         version = 2,
         error_correction = qrcode.constants.ERROR_CORRECT_L,
         box_size=10,
         border=10,)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image()
    #img.show()

    photopath = os.path.join(settings.MEDIA_ROOT, "inspection")
    if not os.path.exists(photopath):
        os.makedirs(photopath)
    path = os.path.join(photopath, 'create.jpg')
    img.save(path)
    return path

THUMBNAIL_WIDTH = 768 # 1024
THUMBNAIL_HEIGHT = 725 # 1000

def get_dailyinspection_path():
    if settings.USE_SAE_BUCKET: #'SERVER_SOFTWARE' in os.environ: 
        return 'dailyinspection'
    else:
        insepection_path = os.path.join(settings.MEDIA_ROOT, 'dailyinspection')
        if not os.path.exists(insepection_path):
            os.makedirs(insepection_path)
        return insepection_path


def save_and_get_image(form, fieldname, instance, obj, required=False):
    in_mem_image_file = form.cleaned_data[fieldname] # new image file
    instance_file = getattr(instance,fieldname, None)  # original file

    if in_mem_image_file:
        # delete original file
        if instance and instance_file and not in_mem_image_file == instance_file:
            instance_file.delete(save=True)       

        if getattr(form, 'clear_' + fieldname, None)():
            # clear original filename
            setattr(obj,fieldname,None)
        else:            
            img = Image.open(in_mem_image_file)
            if img.size[0] > THUMBNAIL_WIDTH or img.size[1] > THUMBNAIL_HEIGHT:
                newWidth = THUMBNAIL_WIDTH
                newHeight = float(THUMBNAIL_WIDTH) / img.size[0] * img.size[1]
                img.thumbnail((newWidth,newHeight),Image.ANTIALIAS)
                filename = image_upload_to_dailyinspection(instance if instance else obj, in_mem_image_file.name)
                filepath = os.path.join(settings.MEDIA_ROOT, filename)
                if not os.path.exists(os.path.dirname(filepath)):
                    os.makedirs(os.path.dirname(filepath))                
                img.save(filepath)
                # set new filename
                setattr(obj,fieldname,filename)
    else:
        if instance: # for update only
            if getattr(form, 'clear_' + fieldname, None)() is None:
                setattr(obj,fieldname,instance_file)  #keep original value
            else:    
                instance_file.delete(save=True) # clear original file

class ThumbnailMixin(object):
    """docstring for ThumbnailMixin"""
    def form_valid(self, form, *args, **kwargs):
        #form.instance = self.get_object(*args, **kwargs)  # without this, form will create another new object
        obj = form.save(commit = False)
        instance = None
        try:
            instance = self.get_object()
        except:
            pass

        if instance: #for update
            obj.id = instance.id
            obj.created = instance.created
            obj.inspector = instance.inspector
            inspection_completed = False
            if obj.is_rectification_completed():
                inspection_completed = True
                if obj.rectification_completed_updated(instance) or obj.turn_completed(instance):
                    log = '{0}-{1} {2}'.format(datetime.datetime.now().strftime('%b-%d-%y %H:%M:%S'),self.request.user,_("uploaded image to complete the inspector").encode("utf-8")) 
                    DailyInspectionLog(dailyinspection=instance,log=log).save()


            if inspection_completed:
                if obj.rectification_completed_updated(instance) or obj.turn_completed(instance):
                    obj.completed_time = timezone.now()
                    obj.rectification_status = 'completed'
                else:
                    obj.completed_time = instance.completed_time
                    obj.rectification_status = instance.rectification_status                    
            else:
                obj.completed_time = None #instance.completed_time
                obj.rectification_status = 'uncompleted' #instance.rectification_status


        save_and_get_image(form, 'image_before', instance, obj, required=True)

        save_and_get_image(form, 'image_after', instance, obj)

        obj.save()

        return HttpResponseRedirect(self.get_success_url())

class DailyInspectionCreateView(StaffRequiredMixin, ThumbnailMixin, CreateView):
    form_class = DailyInspectionForm
    model = DailyInspection
    template_name = "dailyinspection/dailyinspection_create.html"

    # def form_valid(self, form, *args, **kwargs):
    #     messages.success(self.request, _("daily inspection create successfully"), extra_tags='capfirst')
    #     form = super(DailyInspectionCreateView, self).form_valid(form, *args, **kwargs)
    #     return form

    def form_valid(self, form, *args, **kwargs):
        obj = form.save(commit = False)
        obj.inspector = self.request.user
        obj.save()

        messages.success(self.request, _("daily inspection create successfully"), extra_tags='capfirst')

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse("dailyinspection_list", kwargs={}) 

    # def dispatch(self, request, *args, **kwargs):
    #     request.breadcrumbs([
    #         (_("Home"),reverse("home", kwargs={})),
    #         (_("Daily Inspection"),reverse("dailyinspection_list", kwargs={})),
    #         (_('Create'),request.path_info),
    #     ])
    #     return super(DailyInspectionCreateView, self).dispatch(request,args,kwargs)   
        

class DailyInspectionDetailView( DetailView):
    model = DailyInspection
    template_name = "dailyinspection/dailyinspection_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super(DailyInspectionDetailView, self).get_context_data(*args, **kwargs)
        context["fields"] = [field for field in self.model._meta.get_fields() if not field.name in [self.model._meta.pk.attname] and not isinstance(field, ManyToOneRel)]
        context["image_fields"] = ["image_before","image_after"]
        context["display_fields"] = ["category","rectification_status","location"]
        context["fields_exclude"] = []
        context["fields_multichoice"] = ["impact"]
        context["logs"] = DailyInspectionLog.objects.filter(dailyinspection=self.get_object())

        return context

    # def dispatch(self, request, *args, **kwargs):
    #     instance = self.get_object()

    #     request.breadcrumbs([
    #         (_("Home"),reverse("home", kwargs={})),
    #         (_("Daily Inspection"),reverse("dailyinspection_list", kwargs={})),
    #         (instance,request.path_info),
    #     ])
    #     return super(DailyInspectionDetailView, self).dispatch(request,args,kwargs)   
        
class DailyInspectionUpdateView(StaffRequiredMixin, ThumbnailMixin, UpdateView): #ModelFormMixin
    
    model = DailyInspection
    template_name = "dailyinspection/dailyinspection_update.html"
    form_class = DailyInspectionForm

    def get_context_data(self, *args, **kwargs):
        context = super(DailyInspectionUpdateView, self).get_context_data(*args, **kwargs)
        object = self.get_object()
        context["object"] =object 
        #selected = [item for item in object.impact]
        #initial=selected
        form = kwargs.get('form',None) # called in form_invalid
        if form is None:
            form = self.form_class(self.request.POST or None, self.request.FILES or None, instance = self.get_object())
        context["form"] = form
        #context["media"] = settings.MEDIA_URL
        return context        

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        # self.object = self.get_object(*args, **kwargs)

        if form.is_valid():
            messages.success(request, _("daily inspection updated successfully"), extra_tags='capfirst')
            messages.info(request, _("check content please"))

            return self.form_valid(form)
        else:
            messages.error(request, _("daily inspection updated fail"), extra_tags='alert-error')
            return self.form_invalid(form)

        return super(DailyInspectionUpdateView, self).post(request, *args, **kwargs) 

    # def dispatch(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     request.breadcrumbs([
    #         (_("Home"),reverse("home", kwargs={})),
    #         (_("Daily Inspection"),reverse("dailyinspection_list", kwargs={})),
    #         (self.object,request.path_info),
    #     ])
    #     return super(DailyInspectionUpdateView, self).dispatch(request,args,kwargs)   

    def get_success_url(self):
        return reverse("dailyinspection_detail", kwargs={'pk':self.kwargs.get("pk")})

class DailyInspectionDeleteView( StaffRequiredMixin, DeleteView):
    model = DailyInspection
    template_name = "dailyinspection/dailyinspection_delete.html"

    def get_success_url(self):
        return reverse("dailyinspection_list", kwargs={})

'''
operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE BINARY %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE BINARY %s',
        'endswith': 'LIKE BINARY %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }
'''


# From the Migrating to 2.0 guide, Filter.name renamed to Filter.field_name (#792)
class InsepctionFilter(FilterSet):
    #cateory = CharFilter(name='category', lookup_expr='icontains', distinct=True)
    category = MultipleChoiceFilter(field_name ='category', choices=DailyInspection.daily_insepction_category, distinct=True)
    #category = MethodFilter(name='category', action='category_filter', distinct=True)
    #category_id = CharFilter(name='categories__id', lookup_expr='icontains', distinct=True)
    rectification_status = CharFilter(field_name ='rectification_status', lookup_expr='exact', distinct=True)
    # due_date = MethodFilter(name='due_date', action='overdue_filter', distinct=True)
    owner = CharFilter(field_name ='owner', lookup_expr='icontains', distinct=True)

    start = CharFilter(field_name ='created', lookup_expr='gte', distinct=True)
    end = CharFilter(field_name ='created', lookup_expr='lte', distinct=True)

    class Meta:
        model = DailyInspection
        fields = [
            'category',
            'owner',
            'rectification_status',
            'created'
            
        ]

    def category_filter(self, queryset, value):

        qs = queryset
        for category in value:
            # print category
            qs = qs.filter(category=category)

        return qs.distinct()

    # def overdue_filter(self, queryset, value):

    #     qs = queryset
    #     for due_date in value:
    #         qs = qs.filter(due_date__lt=due_date)

    #     return qs.distinct()

class FilterMixin(object):
    filter_class = None
    search_ordering_param = "ordering"

    def get_queryset(self, *args, **kwargs):
        try:
            qs = super(FilterMixin, self).get_queryset(*args, **kwargs)
            return qs
        except:
            raise ImproperlyConfigured("You must have a queryset in order to use the FilterMixin")

    def get_context_data(self, *args, **kwargs):
        context = super(FilterMixin, self).get_context_data(*args, **kwargs)
        qs = self.get_queryset()
        ordering = self.request.GET.get(self.search_ordering_param, '-created')
        if qs and ordering:
            qs = qs.order_by(ordering)
        filter_class = self.filter_class
        if qs and filter_class:
            f = filter_class(self.request.GET, queryset=qs)
            context["object_list"] = f.qs # f also works
            context["object_list_count"] = f.qs.count()
        return context

class ChartMixin(object):

    def get_context_data(self, *args, **kwargs):
        context = super(ChartMixin, self).get_context_data(*args, **kwargs)
        object_list = context["object_list"]
        data = { 
            'datasets': [{
                # 'label': '# of Votes',
                'data': [object_list.filter(category=category[0]).count() if not object_list is None else 0 for category in DailyInspection.daily_insepction_category],
                'backgroundColor': [
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',
                ]            
            }],

            # These labels appear in the legend and in the tooltips when hovering different arcs
            'labels': [_(category[1]) for category in DailyInspection.daily_insepction_category], # why ugettext in models.py didn't work?
        };
        context["data"] = json.dumps(data)
        
        return context

class DailyInspectionListView(ChartMixin, FilterMixin, ListView): 
    model = DailyInspection
    template_name = "dailyinspection/dailyinspection_list.html"
    filter_class = InsepctionFilter

    def get_context_data(self, *args, **kwargs):
        context = super(DailyInspectionListView, self).get_context_data(*args, **kwargs)
        # context["objects_list"] = DailyInspection.objects.order_by('-updated')
        context["objects_sort"] = DailyInspection.objects.order_by('-updated')[:10]
        context["query"] = self.request.GET.get("q")
        context["InspectionFilterForm"] = InspectionFilterForm(data=self.request.GET or None)        
        context["categories"] = DailyInspection.daily_insepction_category

        # print context['data']
        return context       

    def get_queryset(self, *args, **kwargs):
        qs = super(DailyInspectionListView, self).get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        overdue = self.request.GET.get("overdue")

        qs  = None
        if not self.request.user.is_staff and not self.request.user.is_superuser:
            qs =  self.model.objects.external()
        else:
            qs =  self.model.objects.all()

        # for over due only
        if overdue:
            qs = qs.filter(due_date__lt=timezone.now()).filter(rectification_status="uncompleted")
            return qs
        
        if query:
            qs = qs.filter(
                Q(impact__icontains=query) |
                Q(rectification_measures__icontains=query) |
                Q(owner__icontains=query) |
                Q(category__icontains=query) |
                Q(inspection_content__icontains=query)
                )
            try:
                qs2 = qs.filter(
                    Q(rectification_status=query)
                )
                qs = (qs | qs2).distinct()
            except:
                pass
        return qs

    def post(self, *args, **kwargs):

        # from plugin.zips import ZipUtilities
        # utilities = ZipUtilities()
        # for file_obj in file_objs:
        #    tmp_dl_path = os.path.join(path_to, filename)
        #    utilities.toZip(tmp_dl_path, filename)
        # #utilities.close()

        import zipfile
        import os 
        from plugin.zips import gen_zip_with_zipfile

        if 0:
            path_to = "document"
            f = gen_zip_with_zipfile(path_to,'..\\abcd.zip')
            f.close()
            # response = HttpResponse(f.fp, content_type='application/zip')
            fread = open(f.filename,"rb")        
            response = HttpResponse(fread, content_type='application/zip')        
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format("download.zip")
            fread.close()
            return response


        if 0:
            # from django.core.servers.basehttp import FileWrapper
            from wsgiref.util import FileWrapper
            import tempfile
            temp = tempfile.TemporaryFile() 
            # temp.close()
            # temp = "a.zip"
            archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) 
            # for index in range(10):  
            #     filename = ".\\document\\ckeditor.md"
            #     archive.write(filename, 'file%d.txt' % index)  
            archive.write(".\\document\\ckeditor.md") 
            # src = "document"
            # files = os.listdir(src) 
            # for filename in files: 
            #     archive.write(os.path.join(src, filename), filename) 
            #     print os.path.join(src, filename), filename
            archive.close() 

            # path_to = ".\\document"
            # f = gen_zip_with_zipfile(path_to, temp)
            # f.close()

            wrapper = FileWrapper(temp) 
            response = HttpResponse(wrapper, content_type='application/zip') 
            response['Content-Disposition'] = 'attachment; filename=test.zip' 
            response['Content-Length'] = temp.tell() 
            temp.seek(0) 
            return response 


        if 0:
            import StringIO
            # Files (local path) to put in the .zip
            # FIXME: Change this (get paths from DB etc)
            filenames = [".\\document\\ckeditor.md",]

            # Folder name in ZIP archive which contains the above files
            # E.g [thearchive.zip]/somefiles/file2.txt
            # FIXME: Set this to something better
            zip_subdir = "somefiles"
            zip_filename = "%s.zip" % zip_subdir

            # Open StringIO to grab in-memory ZIP contents
            s = StringIO.StringIO()

            # The zip compressor
            zf = zipfile.ZipFile(s, "w")

            for fpath in filenames:
                # Calculate path for file in zip
                fdir, fname = os.path.split(fpath)
                zip_path = os.path.join(zip_subdir, fname)

                # Add file, at correct path
                zf.write(fpath, zip_path)

            # Must close zip for all contents to be written
            zf.close()

            # Grab ZIP file from in-memory, make response with correct MIME-type
            resp = HttpResponse(s.getvalue(), content_type='application/zip') 
            # ..and correct content-disposition
            resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

            return resp

        if 0:
            from django.http import StreamingHttpResponse
            from plugin.zips import gen_zip_with_zipfile
            response = StreamingHttpResponse(f, content_type='application/zip')
            response = HttpResponse(FileWrapper(f.fp.getvalue()), content_type='application/zip') 

        qs = self.get_queryset()
        f = self.filter_class(self.request.GET, queryset=qs)

        if 0:
            import StringIO
            s = StringIO.StringIO()
            zf = zipfile.ZipFile(s, "w")   
            zip_subdir = "media"
            for obj in f.qs:
                path = obj.image_before.path
                fdir, fname = os.path.split(path)
                zip_path = os.path.join(zip_subdir, path[len(settings.MEDIA_ROOT)+1:])            
                zf.write(path, zip_path)

                if obj.image_after:
                    path = obj.image_after.path
                    fdir, fname = os.path.split(path)
                    zip_path = os.path.join(zip_subdir, path[len(settings.MEDIA_ROOT)+1:])            
                    zf.write(path, zip_path)

            from plugin.utils import gen_csv_file
            import tempfile
            # temp = tempfile.TemporaryFile(mode='w+t')
            # temp = tempfile.mkdtemp()
            temp = tempfile.NamedTemporaryFile()
            temp.close()

            fields_display = [ "category", "rectification_status", "location" ]
            fields_fk = ["inspector",  ]
            fields_datetime = ["due_date","created", "updated","completed_time"]
            excludes = [field.name for field in self.model._meta.get_fields() if isinstance(field, models.ManyToOneRel)]
            fields_multiple = ["impact",]        
            gen_csv_file(self.model, f.qs, temp.name, fields_display, fields_fk, fields_datetime, excludes, fields_multiple)

            zf.write(temp.name, "daily_inspection_export.csv")
            os.remove(temp.name)

            zf.close()
            resp = HttpResponse(s.getvalue(), content_type='application/zip')  
            resp['Content-Disposition'] = 'attachment; filename=%s' % "daily_inspection_export.zip"
            return resp

        if 1:
            from django.http import StreamingHttpResponse
            import zipstream

            zf = zipstream.ZipFile(mode='w', compression=zipfile.ZIP_DEFLATED)
            zip_subdir = "media"
            for obj in f.qs:
                path = obj.image_before.path
                fdir, fname = os.path.split(path)
                zip_path = os.path.join(zip_subdir, path[len(settings.MEDIA_ROOT)+1:])            
                zf.write(path, zip_path)

                if obj.image_after:
                    path = obj.image_after.path
                    fdir, fname = os.path.split(path)
                    zip_path = os.path.join(zip_subdir, path[len(settings.MEDIA_ROOT)+1:])            
                    zf.write(path, zip_path)


            from plugin.utils import gen_csv_file
            import tempfile
            # temp = tempfile.TemporaryFile(mode='w+t')
            # temp = tempfile.mkdtemp()
            temp = tempfile.NamedTemporaryFile()
            temp.close()

            fields_display = [ "category", "rectification_status", "location" ]
            fields_fk = ["inspector",  ]
            fields_datetime = ["due_date","created", "updated","completed_time"]
            excludes = [field.name for field in self.model._meta.get_fields() if isinstance(field, models.ManyToOneRel)]
            fields_multiple = ["impact",]        
            gen_csv_file(self.model, f.qs, temp.name, fields_display, fields_fk, fields_datetime, excludes, fields_multiple)

            zf.write(temp.name, "daily_inspection_export.csv")            

            response = StreamingHttpResponse(zf, content_type='application/zip')            
            response['Content-Disposition'] = 'attachment; filename={}'.format('daily_inspection_export.zip')
            # zf.close()
            # os.remove(temp.name)
            return response


        # from plugin.utils import gen_csv
        # return gen_csv(self.model, f.qs, "daily_inspection_export.csv", fields_display, fields_fk, fields_datetime, excludes, fields_multiple)
        
    # def dispatch(self, request, *args, **kwargs):
    #     request.breadcrumbs([
    #         (_("Home"),reverse("home", kwargs={})),
    #         (_('Daily Inspection'),request.path_info),
    #     ])
    #     return super(DailyInspectionListView, self).dispatch(request,args,kwargs)   

# https://github.com/novafloss/django-chartjs
class LineChartColorMixin(object):
    def get_context_data(self):
        data = super(LineChartColorMixin, self).get_context_data()
        backgroundColors =[
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',                    
                ]

        borderColors =[
                    'rgba(255, 0, 0, 0.1)',
                    'rgba(0, 255, 0, 0.1)',
                    'rgba(0, 0, 255, 0.1)',
                    'rgba(220, 0, 255, 0.1)',
                    'rgba(0, 220, 255, 0.1)',                    
                ]                

        for i in range(0,len(self.get_providers())):
        #for i, color in enumerate(backgroundColors)
            data['datasets'][i]['backgroundColor'] = backgroundColors[i]
            data['datasets'][i]['borderColor'] = borderColors[i]

        # print data
        return data 

class StatMixin(object):

    # ['category']['date']['count']
    # {'people',{'2017-08-01':'0','2017-08-02':'1'}}

    def get_dates(self):
        #dates = list([ ins.created.strftime("%Y-%m-%d") for ins in DailyInspection.objects.order_by('-updated')])        
        dates = list([ ins.get_created_date() for ins in DailyInspection.objects.order_by('-updated')[:30]])
        dates = list(set(dates))
        dates.sort()
        return dates

    def get_dates_value(self):
        dates = list([ ins.created for ins in DailyInspection.objects.order_by('-updated')[:30]])
        dates = list(set(dates))
        dates.sort()
        return dates

    def get_catetory(self):
        categories = list([ ins[1] for ins in DailyInspection.daily_insepction_category])
        return categories

    def get_catetory_value(self):
        categories = list([ ins[0] for ins in DailyInspection.daily_insepction_category])
        return categories

    def get_chart_counts(self):
        counts = []
        dates = self.get_dates()
        categories = self.get_catetory_value()
        for category in categories:
            count  = [DailyInspection.objects.filter(created__range=(\
                            datetime.datetime( datetime.datetime.strptime(date,'%Y-%m-%d').year, datetime.datetime.strptime(date,'%Y-%m-%d').month,datetime.datetime.strptime(date,'%Y-%m-%d').day,0,0,0),\
                            datetime.datetime(datetime.datetime.strptime(date,'%Y-%m-%d').year, datetime.datetime.strptime(date,'%Y-%m-%d').month,datetime.datetime.strptime(date,'%Y-%m-%d').day,23,59,59)))\
                                             .filter(category=category).count() for date in dates ]
            if counts == None:
                counts = [count]
            else:
                counts.append(count)
        return counts


    def get_counters_sorted(self):
        llcounterperdaypercategory = {}
        for category in self.get_catetory():
            #llcounterperdaypercategory.update({category:{}})
            llcounterperdaypercategory[category] = {}
            for date in self.get_dates():
                llcounterperdaypercategory[category].update({date:0})

        return self.get_counters(llcounterperdaypercategory)

    def get_counters(self, llcounterperdaypercategory):
        #llcounterperdaypercategory = {}
        for inspect in DailyInspection.objects.all():
            created = inspect.get_created_date()
            category = inspect.my_get_field_display('category')
            if llcounterperdaypercategory.get(category, None) is None:
                llcounterperdaypercategory.update({category: {created : 1}})
            else:                
                if llcounterperdaypercategory[category].get(created, None):
                    llcounterperdaypercategory[category][created] = llcounterperdaypercategory[category].get(created, None) + 1
                else:
                    llcounterperdaypercategory[category].update({created:1})

        return llcounterperdaypercategory


#class ShelfInspectionStatView(TemplateView):
class DailyInspectionStatView(StatMixin, TemplateResponseMixin, ContextMixin, View):
    template_name = "dailyinspection/dailyinspection_stat.html"

    def get_context_data(self, *args, **kwargs):
        context = super(DailyInspectionStatView, self).get_context_data(*args, **kwargs)
        context["objects_list"] = DailyInspection.objects.order_by('-updated')
        context["dates"] = self.get_dates()
        context["categories"] = self.get_catetory()
        context["counters"] = self.get_counters_sorted()
        return context   

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    # def dispatch(self, request, *args, **kwargs):
    #     request.breadcrumbs([
    #         (_("Home"),reverse("home", kwargs={})),
    #         (_('Inspection List'),reverse("dailyinspection_list", kwargs={})),
    #         (_('Inspection Statistic'),request.path_info),
    #     ])
    #     return super(DailyInspectionStatView, self).dispatch(request,args,kwargs)  

class LineChartJSONView(StatMixin, LineChartColorMixin, BaseLineChartView):
    def get_labels(self):
        """Return labels for the x-axis."""
        return self.get_dates()

    def get_providers(self):
        """Return names of datasets."""
        return self.get_catetory()

    def get_data(self):
        """Return 3 datasets to plot."""
        return self.get_chart_counts()


# var data = {
#     labels : ["January","February","March","April","May","June","July"],
#     datasets : [
#         {
#             fillColor : "rgba(220,220,220,0.5)",
#             strokeColor : "rgba(220,220,220,1)",
#             data : [65,59,90,81,56,55,40]
#         },
#         {
#             fillColor : "rgba(151,187,205,0.5)",
#             strokeColor : "rgba(151,187,205,1)",
#             data : [28,48,40,19,96,27,100]
#         }
#     ]
# }

class OverdueChartJSONView(JSONView):

    def get_context_data(self):
        data = { 
            'datasets': [{
                # 'label': '# of Votes',
                'data': [DailyInspection.objects.filter(rectification_status="uncompleted", due_date__lt=timezone.now(), category=category[0]).count() for category in DailyInspection.daily_insepction_category]\
                if self.request.user.is_staff else \
                    [0 for category in DailyInspection.daily_insepction_category],
                'backgroundColor': [
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',
                ]            
            }],

            # These labels appear in the legend and in the tooltips when hovering different arcs
            'labels': [category[1] for category in DailyInspection.daily_insepction_category],
        };

        return data

class LastsChartJSONView(LineChartColorMixin, BaseLineChartView):
    def get_time_range(self):
        times =  [timezone.now(), timezone.now() - timedelta(weeks=1)]
        return times
               
    def get_labels(self):
        """Return labels for the x-axis."""
        return [category[1] for category in DailyInspection.daily_insepction_category]

    def get_providers(self):
        """Return names of datasets."""
        providers =  [ "{0}  ~  {1}".format(self.get_time_range()[1].date(), self.get_time_range()[0].date()), ]
        return providers

    def get_data(self):
        data =  [[DailyInspection.objects.filter(category=category[0], created__gte=self.get_time_range()[1]).count()\
                if self.request.user.is_staff else \
                DailyInspection.objects.filter(rectification_status="completed", category=category[0], created__gte=self.get_time_range()[1]).count()\
                     for category in DailyInspection.daily_insepction_category],]
        return data

class CompareChartJSONView(LineChartColorMixin, BaseLineChartView):
    def get_last_times(self):
        #  RuntimeWarning: DateTimeField DailyInspection.created received a naive datetime (2017-12-02 23:59:59) while time zone support is active.
        year = timezone.now().year #time.localtime()[0]
        month = timezone.now().month #time.localtime()[1]        
        return [[month-i or 12, year if month > i else year-1] for i in reversed(range(0,1))]
               
    def get_labels(self):
        """Return labels for the x-axis."""
        return [category[1] for category in DailyInspection.daily_insepction_category]

    def get_providers(self):
        """Return names of datasets."""
        return [            
            "{0}-{1:0>2d}".format(year,month) for month,year in self.get_last_times()
        ]

    def get_data(self):
        data =  [[DailyInspection.objects.filter(category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count() \
                if self.request.user.is_staff else \
                DailyInspection.objects.filter(rectification_status="completed", category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count()\
                    for category in DailyInspection.daily_insepction_category] \
                        for month, year in self.get_last_times()]
        # data =  [[DailyInspection.objects.filter(category=category[0], created__year=year, created__month=month).count() for category in DailyInspection.daily_insepction_category] \
        #             for month, year in self.get_last_times()]     
        # issue for filter "created__month=month" # https://segmentfault.com/q/1010000009037684
        return data


    # function is same base class, color is different , to be improved
    def get_context_data(self):
        data = super(CompareChartJSONView, self).get_context_data()
        backgroundColors =[
                    # 'rgba(255, 0, 0, 0.2)',
                    # 'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',                    
                ]

        borderColors =[
                    # 'rgba(255, 0, 0, 0.1)',
                    # 'rgba(0, 255, 0, 0.1)',
                    'rgba(0, 0, 255, 0.1)',
                    'rgba(220, 0, 255, 0.1)',
                    'rgba(0, 220, 255, 0.1)',                    
                ]                

        for i in range(0,len(self.get_providers())):
        #for i, color in enumerate(backgroundColors)
            data['datasets'][i]['backgroundColor'] = backgroundColors[i]
            data['datasets'][i]['borderColor'] = borderColors[i]

        return data 

class DashboardViewDailyInspection(APIView):
    authentication_classes = []
    permission_classes = []

    def get_last_times(self):
        year = timezone.now().year #time.localtime()[0]
        return [[i, year] for i in range(1,13)]

    def get(self, request, format=None):
        rows = [[DailyInspection.objects.filter(category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count() for category in DailyInspection.daily_insepction_category] \
                    for month, year in self.get_last_times()]
        columns = [ (month[0], month[1]) for month in month_choice]
        data = {
                "columns": columns,
                "rows": rows,
        }
        return Response(data)    
