from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseRedirect
# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.db import models
from django.forms import models as model_forms
from django.forms.models import (
    ModelForm, 
    modelformset_factory, 
    inlineformset_factory, 
    BaseModelFormSet, 
    BaseInlineFormSet
)
from django.core.paginator import Paginator,PageNotAnInteger, EmptyPage
from django.conf import settings

from plugin.forms import  ImageFileInput


model_map = settings.MODEL_MAP if hasattr(settings, "MODEL_MAP") else {} or  {}
# {
#     'DailyInspection': ['daily_inspection_stat','Daily Inspection'],
#     'Forklift': ['storage_sec','Storage Security'],
#     'Vehicle': ['transport_security','Transport Security'], 
# }

submodel_map = settings.SUBMODEL_MAP  if hasattr(settings, "SUBMODEL_MAP") else {} or {}
# {
#     'ShelfAnnualInspection': ['shelf_inspection_list','shelf inspection'], # add Model homepage
#     'shelf': ['shelf_inspection_list','shelf inspection'],
#     'shelf_inspection_record': ['shelf_inspection_list','shelf inspection'],
#     'ForkliftRepair': ['forklift_list','Forklift'],
#     'ForkliftMaint': ['forklift_list','Forklift'],
#     'ForkliftAnnualInspection': ['forklift_list','Forklift'],
#     'TrainingCourse': ['annualtrainingplan_list','annual training plan'],
#     'TrainingRecord': ['annualtrainingplan_list','annual training plan'],
#     'ExtinguisherInspection': ['extinguisherinspection_list','extinguisher inspection'],
#     'HydrantInspection': ['hydrantinspection_list','hydrant inspection'],    
#     'VehicleSafetyCheckEntry': ['vehiclesafety_list','vehicle safety check'],        
# }

class StaffRequiredMixin(object):
    @classmethod
    def as_view(self, *args, **kwargs):
        view = super(StaffRequiredMixin, self).as_view(*args, **kwargs)
        return login_required(view)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super(StaffRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            #raise Http404
            #return HttpResponseRedirect(reverse('home',kwargs={}))
            return render(request, "permission_alert.html", {})

class SuperRequiredMixin(StaffRequiredMixin):

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		if request.user.is_superuser:
			return super(SuperRequiredMixin, self).dispatch(request, *args, **kwargs)
		else:
			raise Http404

class LoginRequiredMixin(object):
	@classmethod
	def as_view(self, *args, **kwargs):
		view = super(LoginRequiredMixin, self).as_view(*args, **kwargs)
		return login_required(view)

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

#  CRDU can be start from (1) ListView  or (2) foreign object DetailView (3) DetailView > DetailView
# this Class is to solve the back & next url

# for UpdateView, DetailView, DeleteView, the object is exist from the beginning, so at the initial render
# (1) back = object.get_absolute_url_list
# (2) back = foreign_object.get_absolute_url
# next can be set through (A) append in url (B) update in get_success_url
# (1) next = object.get_absolute_url
# (2) next = foreign_object.get_absolute_url

# for CreateView, the object is Empty at the initial render
# (1) back = object.get_absolute_url_list
# (2) back = foreign_object.get_absolute_url  ?

# HOW TO transfer the foreign_object to the foreign_set CRDU 
# for RDU, getattr(object, parent_object_related_name)
# for C, object is not exist at the beginning, using session instead is one solution

# HOW to tell foreign_set CRDU view it's (1) or (2)?
# append paramet isshortcut
# for CreateView, if there's parameter in url, it will Validation at the beginning ???

# CreateView
# parent_object_related_name &  parent_object_model
# navigation, explict next url NOT specified because it will call form validation at the beginning, to be DIG later

# DetailView
# parent_object_related_name & is_root_model (O) & get_absolute_url
# navigation, explict next url specified

# UpdateView, DetailView
# parent_object_related_name, allow_modify=True, allow_edit=True, parent_object_back, get_absolute_url_update, get_absolute_url_delete
# navigation, explict next url specified

class ShortcutURLMixin(object):
    # if this view is created from DetaiView which is the foreign object
    parent_object_related_name = None
    parent_object_model = None # mandatory for CreateView 

    mixin_view_mode = None # internal variable, for double check

    parent_object_back = None

    def get_parent_object_RDU(self, *args, **kwargs):
        if not self.mixin_view_mode in ["detailview","updateview","deleteview"]:
            return None
            
        # (2) SHORTCUT
        # RDU View
        isshortcut = self.request.GET.get("next", None) # not valid after I add edit shortcut on root list view
        if isshortcut:
            if self.parent_object_related_name:
                try:                
                    self.parent_object_back = getattr(self.get_object(), self.parent_object_related_name) # valid for DetailView, UpdateView, DeleteView
                except:
                    pass
                    
        return self.parent_object_back

    def get_parent_object_C(self, *args, **kwargs):
        if not self.mixin_view_mode in ["createview"]:
            return None
            
        parent_object_pk = self.request.session.get("parent_object_pk", None) # NEED better method for CreateView
        isshortcut = parent_object_pk
        try:
            ins = self.get_object()
            if ins.pk == parent_object_pk:
                parent_object_pk = False
        except:
            pass
            
        # C View
        if isshortcut:
            parent_object_pk = self.request.session.get("parent_object_pk", None)
            if parent_object_pk and self.parent_object_related_name and self.parent_object_model:
                # tmp_object = self.model.objects.first()
                # parent_object_model = type(getattr(tmp_object, self.parent_object_related_name))
                try:
                    self.parent_object_back =  self.parent_object_model.objects.get(pk=parent_object_pk)
                except:
                    pass
                
        return self.parent_object_back

                
    def get_context_data(self, *args, **kwargs):
        context = super(ShortcutURLMixin, self).get_context_data(*args, **kwargs)

        self.get_parent_object_C()        
        self.get_parent_object_RDU()
	
        if self.parent_object_back:
            context["parent_object_back"] = self.parent_object_back  
            # NOT USED, we can get the parent object, but I can't judge whether curernt RDU view is from the parent detail view, if I use GET parameter, then why can't I just used GET for navigation
            
        context["back_url"] = self.get_back_url()
        if self.request.GET.get('_popup', None):
            context["popup_view"] = 1
        
        return context        

    def get_back_url(self):
        back_url = None
        parent_object_pk = self.request.session.get("parent_object_pk", None)
        
        if self.request.GET.get('next', None): # RDU
            back_url = self.request.GET.get('next')
        elif  parent_object_pk and self.parent_object_model: # C
            back_url = self.parent_object_model.objects.get(pk=parent_object_pk).get_absolute_url()
        elif  self.request.session.get("shortcut_back_url") and \
                    not self.request.get_full_path() == self.request.session.get("shortcut_back_url"):
            back_url = self.request.session.get("shortcut_back_url")

        _popup = self.request.GET.get('_popup', None)
        if back_url and _popup:
            popupurl =  '_popup=' + _popup
            if "?" in back_url:
                popupurl = "&" + popupurl
            else:
                popupurl = "?" + popupurl
            back_url += popupurl
            
        return back_url

        
    def get_success_url_next(self):
        # foreignset object update
        # method 1: using GET
        next = self.request.GET.get('next')
        if next:
            return next

        # method 2 : using class attribute
        if self.parent_object_back:
            return self.parent_object_back.get_absolute_url()

        # method 3 : using session
        parent_object_pk = self.request.session.get("parent_object_pk", None) 
        if parent_object_pk and self.parent_object_model:
            return self.parent_object_model.objects.get(pk=parent_object_pk).get_absolute_url()

        # method 4 : other
        shortcut_back_url = self.request.session.get("shortcut_back_url", None) 
        if shortcut_back_url:
            return shortcut_back_url

        return None
        return self.get_object().get_absolute_url()

class TableListViewMixin(object):
    mixin_view_mode = "listview"
    
    template_name = "default/list.html"
    
    fields = []
    fields_display = []
    fields_exclude = []
    fields_files = []
    fields_images = []

    foreign_fields_images = []

    def get_context_data(self, *args, **kwargs):
        context = super(TableListViewMixin, self).get_context_data(*args, **kwargs)
        context["fields"] = [field.name for field in self.model._meta.get_fields() if not field.name in [self.model._meta.pk.attname,] and not isinstance(field, models.ManyToOneRel) and not isinstance(field, models.ManyToManyRel) and not field.name in self.fields_exclude] \
                    if not self.fields else self.fields
        context["fields_display"] = self.fields_display
        context["fields_files"] = self.fields_files
        context["fields_images"] = self.fields_images

        context["foreign_fields_images"] = self.foreign_fields_images
        
        return context

    def dispatch(self, request, *args, **kwargs):
        if  self.request.session.get("shortcut_back_url"):
            del self.request.session["shortcut_back_url"]

        if  self.request.session.get("shortcut_back_url_saved"):
            del self.request.session["shortcut_back_url_saved"]
            
        if  self.request.session.get("parent_object_pk"):
            del self.request.session["parent_object_pk"]            

        list = [
            (_("Home"),reverse("home", kwargs={})), 
            (self.model._meta.verbose_name,request.path_info),
        ]
        # if model_map.get(self.model._meta.object_name, None):
        #     value = model_map.get(self.model._meta.object_name, None)
        #     list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

        if submodel_map.get(self.model._meta.object_name, None):
            value = submodel_map.get(self.model._meta.object_name, None)
            list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

        request.breadcrumbs(list)
        return super(TableListViewMixin, self).dispatch(request,args,kwargs)   

# from django.db.models.fields import ManyToOneRel
from django.db import models
class TableDetailViewMixin(ShortcutURLMixin):
    mixin_view_mode = "detailview"
    
    template_name = "default/detail.html"
    
    # fieldsets = [("title",{"fields":("",)}), ]
    fieldsets = []
    fields = []
    fields_display = []
    fields_files = []
    fields_images = []
    fields_exclude = []

    model = None
    is_root_model = False # root foreign which has OneToMany objects

    model_sets = [("model name", None, []),]  # model name, object_list, list_display
    
    def get_context_data(self, *args, **kwargs):
        context = super(TableDetailViewMixin, self).get_context_data(*args, **kwargs)
        if not self.fieldsets:
            context["fields"] = [field for field in self.model._meta.get_fields() if not field.name in self.fields_exclude and not field.name in [self.model._meta.pk.attname,] and not isinstance(field, models.ManyToOneRel) and not isinstance(field, models.ManyToManyRel)] \
                    if not self.fields else self.fields
        # lookup_field
        # _get_non_gfk_field
        # need time to learning
        # pagination :: items_for_result
        context["fieldsets"] = self.fieldsets
        context["fields_display"] = self.fields_display
        context["fields_files"] = self.fields_files
        context["fields_images"] = self.fields_images
        
        context["model_sets"] = self.model_sets

        if not context.get("back_url", None) and self.get_object().get_absolute_url(): # default : get back to list
            try:
                context["back_url"] = self.get_object().get_absolute_url_list()
            except:
                pass
            
        return context        

    def dispatch(self, request, *args, **kwargs):
        if self.is_root_model: # root may include 1st & 2nd level
            self.request.session["parent_object_pk"] = self.get_object().pk
            self.request.session["shortcut_back_url"] = request.get_full_path()   # legacy method

        list = [
            (_("Home"),reverse("home", kwargs={})),
            (self.model._meta.verbose_name, self.get_object().get_absolute_url_list() if hasattr(self.get_object(),"get_absolute_url_list") else ""),            
            (self.get_object(),request.path_info),
        ]

        if submodel_map.get(self.model._meta.object_name, None):
            value = submodel_map.get(self.model._meta.object_name, None)
            list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

        request.breadcrumbs(list)

        return super(TableDetailViewMixin, self).dispatch(request,args,kwargs)    


# fields = ModelFormMixin::fields 

# form_class
# form_class = ModelFormMixin::get_form_class << model_forms.modelform_factory(model, fields=self.fields)
# form_class = FormMixin::get_form_class << self.form_class

# form = FormMixin::get_form()

# kwargs : ModelFormMixin::get_form_kwargs
#       instance :  self.object
# kwargs : FormMixin::get_form_kwargs
#       initial :  self.get_initial()
#       prefix :  self.get_prefix()
#       data : self.request.POST
#       files : self.request.FILES

# success_url : 
#       ModelFormMixin::get_success_url
#       FormMixin::get_success_url

# get_context_data
#       form : FormMixin::get_context_data
class UpdateViewMixin(ShortcutURLMixin):
    mixin_view_mode = "updateview"
    show_breadcrumbs = True
    
    template_name = "default/update.html"

    # model = models.Model
    fields = None # is defined in ModelFormMixin
    exclude = None
    # fields = [field.name for field in model._meta.get_fields() if not field.name in [model._meta.pk.attname,] and not isinstance(field, models.ManyToOneRel)]

    parent_object_field_hidden = True

    def get_form_class(self):

        do_hidden = self.get_parent_object_RDU() and self.parent_object_field_hidden

        if self.fields:
            if do_hidden and self.parent_object_related_name in self.fields:
                self.fields.remove(self.parent_object_related_name)
            self.form_class = model_forms.modelform_factory(self.model, fields=self.fields, form=self.form_class or ModelForm)
        else:
            if not self.exclude:
                if self.form_class and self.form_class.Meta.exclude:
                    self.exclude = self.form_class.Meta.exclude
                else:
                    self.exclude = ["",]            
                    
            if do_hidden:
                if not self.parent_object_related_name in self.exclude:
                    self.exclude.append(self.parent_object_related_name)

            self.form_class = model_forms.modelform_factory(self.model, exclude=self.exclude, form=self.form_class or ModelForm)
        
        return self.form_class

    def get_success_url(self):
        success_url = self.get_success_url_next()
        if success_url:
            return success_url
        else:
            return super(UpdateViewMixin, self).get_success_url()
        
    def get_context_data(self, *args, **kwargs):        
        context = super(UpdateViewMixin, self).get_context_data(*args, **kwargs) 
        context["title"] = self.get_object()

        if not context.get("back_url",None) and self.get_object().get_absolute_url():
            context["back_url"] = self.get_object().get_absolute_url()
        return context

    # HERE just for learning, it was implemented in base classed
    def post(self, request, *args, **kwargs):
        self.object = self.get_object() # must call in advace # called in  BaseUpdateView::post

        form = self.get_form()  # called in FormMixin::get_form
        # form = self.form_class(self.request.POST or None, self.request.FILES or None)        

        if form.is_valid():
            return self.form_valid(form)
        else:            
            return self.form_invalid(form)

        return super(UpdateViewMixin, self).post(request, *args, **kwargs)  

    def form_save_callback(self, instance):
        pass
        
    # copy from FormMixin
    def form_valid(self, form):
        obj = form.save(commit = False)
        self.form_save_callback(obj)
        obj.save()
        self.object = obj
        return HttpResponseRedirect(self.get_success_url())      
        
    # def form_invalid(self, form):
    #     return self.render_to_response(self.get_context_data())

    def get_fields(self, *args, **kwargs):
        return self.fields

        
    def dispatch(self, request, *args, **kwargs):
        if not self.fields and not self.get_fields() and not self.form_class and not self.exclude:
            self.fields = [field.name for field in self.model._meta.get_fields() 
                if not field.name in [self.model._meta.pk.attname,] and 
                   not field.name is self.parent_object_related_name and 
                   not isinstance(field, models.ManyToOneRel)]

        if self.show_breadcrumbs:
            list = [
                (_("Home"),reverse("home", kwargs={})),
                (self.model._meta.verbose_name, self.get_object().get_absolute_url_list() if hasattr(self.get_object(),"get_absolute_url_list") else ""),            
                (self.get_object(),request.path_info),
            ]

            if submodel_map and submodel_map.get(self.model._meta.object_name, None):
                value = submodel_map.get(self.model._meta.object_name, None)
                list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

            request.breadcrumbs(list)

        return super(UpdateViewMixin, self).dispatch(request,args,kwargs)           


class UpdateWithImageSetViewMixin(UpdateViewMixin):
    template_name = "default/update_imageset.html"
    model_foreignset = None # mandatory
    form_foreignset_class = None  # optional
    formset_extra = 1


    def get_foreign_form_class(self):
        if self.form_foreignset_class:
            return self.form_foreignset_class
        else:
            return model_forms.modelform_factory(self.model_foreignset, 
                        fields=["image",], 
                        widgets={"image":ImageFileInput(),})

    def get_inine_foreign_formset_class(self, can_delete=True):
        return inlineformset_factory(
                                    self.model, 
                                    self.model_foreignset,  
                                    form=self.get_foreign_form_class(), 
                                    can_delete=can_delete,
                                    extra=self.formset_extra)

    def get_context_data(self, *args, **kwargs):
        context = super(UpdateWithImageSetViewMixin, self).get_context_data(*args, **kwargs) 

        context["formset"] = self.get_inine_foreign_formset_class()(instance=self.object)
        context["item_name"] = self.model_foreignset._meta.verbose_name

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() 

        form = self.get_form() 
        # form_foreign_image = self.get_foreign_form_class()(self.request.POST, self.request.FILES )
        formset = self.get_inine_foreign_formset_class()(self.request.POST, self.request.FILES, instance=self.object )

        if form.is_valid():
            '''
            if form_foreign_image.is_valid():
                image = form_foreign_image.save(commit=False)
                image.forklift_annual_inspection = self.object
                image.save()
            '''
            if formset.is_valid():
                formset.save()

            return super(UpdateWithImageSetViewMixin, self).form_valid(form)

            form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:            
            return self.form_invalid(form)

        return super(UpdateWithImageSetViewMixin, self).post(request, *args, **kwargs)       


"""
self.object : ModelFormMixin::form_valid
"""

class CreateViewMixin(ShortcutURLMixin):
    mixin_view_mode = "createview"
    show_breadcrumbs = True
    
    template_name = "default/create.html"

    parent_object_field_hidden = True

    exclude = None

    def get_form_class(self):

        do_hidden = self.request.session.get("parent_object_pk", None) and self.parent_object_field_hidden
        if 1: # not self.form_class:
            if self.fields:
                if do_hidden and self.parent_object_related_name in self.fields:
                    self.fields.remove(self.parent_object_related_name)
                self.form_class = model_forms.modelform_factory(self.model, fields=self.fields, form=self.form_class or ModelForm)
            else:
                if do_hidden:
                    if not self.exclude:
                        self.exclude = [self.parent_object_related_name, ]
                    elif not self.parent_object_related_name in self.exclude:
                        self.exclude.append(self.parent_object_related_name)
                else:
                    print ("CreateViewMixin self.exclude #1", self.exclude,)
                    if self.exclude:
                        pass
                    elif not self.exclude and self.form_class and self.form_class.Meta.exclude:
                        self.exclude = self.form_class._meta.exclude
                    else:
                        self.exclude = ["",]

                print ("CreateViewMixin self.exclude #2", self.exclude,)
                self.form_class = model_forms.modelform_factory(self.model, exclude=self.exclude, form=self.form_class or ModelForm)
        
        return self.form_class

    def get_form_kwargs(self):
        kwargs = super(CreateViewMixin, self).get_form_kwargs()
        kwargs.update({
            'initial': self.get_initial(),
        })
        return kwargs
    
    def get_initial(self):
        if  not self.parent_object_field_hidden and self.request.session.get("parent_object_pk"):
            return {self.parent_object_related_name: self.parent_object_model.objects.filter(pk=self.request.session.get("parent_object_pk")).first()}
        else:
            return {}
        
    def get_success_url(self):
        success_url = self.get_success_url_next()
        if success_url:
            return success_url
        else:
            # return self.get_object().get_absolute_url()
            return self.model().get_absolute_url_list()
            return super(CreateViewMixin, self).get_success_url()
        

    def get_context_data(self, *args, **kwargs):
        context = super(CreateViewMixin, self).get_context_data(*args, **kwargs) 

        
        if self.request.method == "GET":
            context["form"] = self.get_form_class()(self.request.GET or None, **self.get_form_kwargs())

        if not context.get("back_url",None) and hasattr(self.model(),"get_absolute_url_list"):
            context["back_url"] = self.model().get_absolute_url_list()
        return context

        
        return context

    def form_invalid(self, form):
        self.object = None
        return super(CreateViewMixin, self).form_invalid(form)

    # copy from "ModelFormMixin::form_valid"
    """
    def form_valid(self, form):
        self.object = form.save()
        return super(CreateViewMixin, self).form_valid(form)
    """

    def form_save_callback(self, instance):
        pass
        
    def form_valid(self, form, *args, **kwargs):
        obj = form.save(commit = False)
        self.form_save_callback(obj)
        pk = self.request.session.get("parent_object_pk", None)
        if pk:
            parent_instance = self.parent_object_model.objects.get(pk=pk)
            setattr(obj, self.parent_object_related_name, parent_instance)
        obj.save()
        self.object = obj

        return HttpResponseRedirect(self.get_success_url())        

    ''' for learning
    def post(self, request, *args, **kwargs):

        form = self.get_form() 

        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            
            return self.form_valid(form) # equal to the two lines below in ModelFormMixin::form_invalid
            self.object = obj
            return HttpResponseRedirect(self.get_success_url())
        else:
            self.object = None
            return self.form_invalid(form)

        return super(CreateViewMixin, self).post(request, *args, **kwargs)  
    '''

    def dispatch(self, request, *args, **kwargs):
        if self.show_breadcrumbs:
            list = [
                (_("Home"),reverse("home", kwargs={})),
                (self.model._meta.verbose_name, self.model().get_absolute_url_list() if hasattr(self.model(),"get_absolute_url_list") else ""),
                (_("Create"),request.path_info),
            ]

            if submodel_map and submodel_map.get(self.model._meta.object_name, None):
                value = submodel_map.get(self.model._meta.object_name, None)
                list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

            request.breadcrumbs(list)

        return super(CreateViewMixin, self).dispatch(request,args,kwargs)                

class DeleteViewMixin(ShortcutURLMixin):
    mixin_view_mode = "deleteview"
    show_breadcrumbs = True
    
    template_name = "default/delete.html"

    # model = models.Model
    fields = None

    def get_success_url(self):
        success_url = self.get_success_url_next()
        if success_url:
            return success_url
        else:
            return self.get_object().get_absolute_url_list()
            return super(DeleteViewMixin, self).get_success_url()
            
    def get_context_data(self, *args, **kwargs):
        context = super(DeleteViewMixin, self).get_context_data(*args, **kwargs) 
        context["title"] = self.get_object()

        if self.get_object().get_absolute_url():
            context["back_url"] = self.get_object().get_absolute_url()
        else:
            if not context.get("back_url",None):
                if self.get_object().get_absolute_url_list():
                    context["back_url"] = self.get_object().get_absolute_url_list()
        return context

        
    def dispatch(self, request, *args, **kwargs):
        if self.show_breadcrumbs:
            list = [
                (_("Home"),reverse("home", kwargs={})),
                (self.model._meta.verbose_name, self.get_object().get_absolute_url_list() if hasattr(self.get_object(),"get_absolute_url_list") else ""),            
                (self.get_object(),request.path_info),
            ]

            if submodel_map and submodel_map.get(self.model._meta.object_name, None):
                value = submodel_map.get(self.model._meta.object_name, None)
                list.insert(1, [_(value[1]), reverse(value[0], kwargs={})])

            request.breadcrumbs(list)

        return super(DeleteViewMixin, self).dispatch(request,args,kwargs)                   

class PaginationMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super(PaginationMixin, self).get_context_data(*args, **kwargs)

        object_list= context["object_list"]

        getvars = self.request.GET.copy()
        if 'page' in getvars:
            del getvars['page']
        if 'pagenum_perpage' in getvars:
            del getvars['pagenum_perpage']
        if len(getvars.keys()) > 0:
            context['getvars'] = "&%s" % getvars.urlencode()
        else:
            context['getvars'] = ''

        pagenum_perpage = self.request.GET.get('pagenum_perpage', None)
        if pagenum_perpage and pagenum_perpage.isdigit():
            pagenum_perpage = int(pagenum_perpage)
        else:
            pagenum_perpage = 10

        paginator = Paginator(object_list, pagenum_perpage)
        records = None
        page = self.request.GET.get('page')

        try:
            records = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            records = paginator.page(1)
            page = 1
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            records = paginator.page(paginator.num_pages)
            page = paginator.num_pages

        page_value = int(page)
        context["start"] = pagenum_perpage*(page_value-1) + 1
        context["end"] = pagenum_perpage * page_value if not page == paginator.num_pages else object_list.count()
        context["total"] = object_list.count()
        context["total_page"] = paginator.num_pages
        display_pages = []
        for page in range(1,6):
            ipage = ((page_value-1)/5)*5 + page
            # print (ipage, paginator.num_pages)
            if not ipage > paginator.num_pages:
                display_pages.append(ipage)
            else:
                break
        context["pages"] = display_pages
        # context["pages"] = [((page_value-1)/5)*5+1, ((page_value-1)/5)*5+2, ((page_value-1)/5)*5+3,((page_value-1)/5)*5+4,((page_value-1)/5)*5+5]
        context["page_highlight"] = page_value
        context["page"] = page_value if page_value else page
        context["pagenum_perpage"] = pagenum_perpage

        context["object_list"] = records

        return context