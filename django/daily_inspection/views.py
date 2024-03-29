from django.shortcuts import render, get_object_or_404, redirect
try:
    from django.core.urls import reverse
except:
    from django.urls import reverse
from django.views.generic.base import View, TemplateResponseMixin, ContextMixin, TemplateView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin, ModelFormMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.db import models
from django.forms import models as model_forms
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from django_filters import FilterSet, CharFilter, NumberFilter, BooleanFilter, MultipleChoiceFilter # MethodFilter, 

from datetime import timedelta

from django.db.models.fields.related import (
    ForeignObjectRel, ManyToOneRel, OneToOneField,#add_lazy_relation,
)

from PIL import Image

import time, datetime
import os

from plugin.var import month_choice
from plugin.qrcode import gen_qrcode
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

from .charts import ChartMixin

from .mixins import StatMixin  

# Create your views here.

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
