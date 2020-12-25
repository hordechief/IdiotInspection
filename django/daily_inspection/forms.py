from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import BaseFormSet,BaseModelFormSet, formset_factory
from django.forms.models import modelformset_factory
from django.contrib.admin import widgets                                       
from django.forms.widgets import Media
from django.contrib.admin.templatetags.admin_static import static
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    DailyInspection,
)

from plugin.forms import  ImageFileInput

RESULT_OPTION = (
    ('yes', 'Yes'),
    ('no', 'No'),
)

# https://docs.djangoproject.com/en/1.3/ref/forms/fields/#django.forms.ModelChoiceField
# https://docs.djangoproject.com/en/1.3/ref/forms/fields/#modelmultiplechoicefield

def get_user_choice_list():
    CHOICE_LIST = []
    # objects.all() will cache
    for ins in get_user_model()._default_manager.all():
        if not (ins, ins) in CHOICE_LIST:
            CHOICE_LIST.append((ins, ins))
    # CHOICE_LIST.sort()
    CHOICE_LIST.insert(0, ('', '----'))

    return CHOICE_LIST

class DailyInspectionForm(forms.ModelForm):
    

    try: # may report error in fresh migrations from scratch
        impact = forms.MultipleChoiceField(
                label=_('Impact'),
                choices = lambda: (item for item in DailyInspection.daily_insepction_impact),
                widget = forms.SelectMultiple(),
                #widget=forms.CheckboxSelectMultiple(),
                initial = ['environment'],
                #initial= lambda: [item for item in DailyInspection.daily_insepction_impact if item],
                required=True
                )

        # owner = forms.ModelChoiceField(
        #         label=_('Owner'),
        #         queryset=get_user_model().objects.all(),
        #         # empty_label = None, #not show enmpty
        #         required=True
        #         )  
         
    except:
        pass     

    owner = forms.ChoiceField(
            label=_('Owner'),
            choices = get_user_choice_list(),
            required=False
            )    

    def __init__(self, *args, **kwargs):
        super(DailyInspectionForm, self).__init__(*args, **kwargs)
        self.fields['due_date'].widget = widgets.AdminDateWidget()

        self.fields['owner'] = forms.ChoiceField(
            label=_('Owner'),
            required=True,
            choices=get_user_choice_list() )

        for field in self.fields.values():
            if not field in self.Meta.exclude:
                if 'class' in field.widget.attrs.keys():
                    field.widget.attrs['class'] = field.widget.attrs['class'] + ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'

    def clear_image_after(self):
        if self.data.get('image_after-clear'):
            return "on"
        return None

    def clear_image_before(self):
        if self.data.get('image_before-clear'):
            return "on"
        return None

    def clean_image_before(self):
        if not self.cleaned_data['image_before']:
            raise forms.ValidationError(_('Picture before Rectification can not be deleted'))

        return self.cleaned_data["image_before"]

    def clean_image_after(self):
        if not self.instance.id and self.cleaned_data['image_after']:
            raise forms.ValidationError(_('picture after rectification should not be exist during creation'))

        return self.cleaned_data["image_after"]

    def clean(self):
        if self.clear_image_before() == 'on':
            raise forms.ValidationError(_('Picture before Rectification can not be deleted'))

        return super(DailyInspectionForm, self).clean()

    class Meta:
        model = DailyInspection

        exclude = [
            'timestamp',
            'updated',
            'rectification_status',
            'inspector',
            'completed_time'
        ]
        
    class Media:
        css = {
            'all': ('admin/css/base.css','admin/css/forms.css','css/form_horizontal_layout.css',),
        }
        #js = ['js/form_horizontal_layout.js']


    #inherit from BaseForm
    @property
    def media(self):
        """
        Provide a description of all media required to render the widgets on this form
        """        
        media = Media(js=[static('js/jquery.init.both.js'), '/admin/jsi18n/', static('admin/js/core.js')])
        for field in self.fields.values():
            for item in field.widget.media._js:
                if not item.split('/')[-1] in ''.join(media._js):
                    media = media + Media(js=[item])

        media = media + Media(self.Media)

        return media

    # ModelChoiceField

class DailyInspectionAdminForm(forms.ModelForm): 

    try: # may report error in fresh migrations from scratch

        impact = forms.MultipleChoiceField(
                label=_('Impact'),
                choices = lambda: (item for item in DailyInspection.daily_insepction_impact),
                widget = forms.SelectMultiple(),
                #widget=forms.CheckboxSelectMultiple(),
                initial = ['environment'],
                #initial= lambda: [item for item in DailyInspection.daily_insepction_impact if item],
                required=True
                )   

        owner = forms.ChoiceField(
                label=_('Owner'),
                choices = set((dailyinspection.owner,dailyinspection.owner) for dailyinspection in DailyInspection.objects.all()),
                # widget=forms.RadioSelect(),
                # initial = None,
                # required=False
                )    
    except:
        pass

class InspectionFilterForm(forms.Form):
    q = forms.CharField(label=_('Search'), required=False)

    '''
    category_id = forms.ModelMultipleChoiceField(
        label='Category',
        queryset=Category.objects.all(), 
        widget=forms.CheckboxSelectMultiple, 
        required=False)
    '''

    category = forms.MultipleChoiceField(
            label=_('Category'),
            choices = DailyInspection.daily_insepction_category,
            #widget = forms.SelectMultiple(),
            widget=forms.CheckboxSelectMultiple(),
            initial = None,
            required=False
            )

    rectification_status = forms.ChoiceField(
            label=_('Rectification Status'),
            choices = DailyInspection.daily_insepction_correction_status,
            widget=forms.RadioSelect(),
            required=False
            )   

    # overdue = forms.BooleanField(
    #         label=_('Overdue'),
    #         # widget=forms.RadioSelect(),
    #         required=False
    #         )   

    try:
        # CHOICE_LIST = set((dailyinspection.owner,dailyinspection.owner) for dailyinspection in DailyInspection.objects.all())

        CHOICE_LIST = []
        # for ins in DailyInspection.objects.all():
        #     if not (ins.owner, ins.owner) in CHOICE_LIST:
        #         CHOICE_LIST.append((ins.owner, ins.owner))
        for ins in get_user_model().objects.all():
            if not (ins, ins) in CHOICE_LIST:
                CHOICE_LIST.append((ins, ins))                
        CHOICE_LIST.sort()
        CHOICE_LIST.insert(0, ('', '----'))

        owner = forms.ChoiceField(
                label=_('Owner'),
                choices = CHOICE_LIST,
                # widget=forms.RadioSelect(),
                widget=forms.Select(),
                initial = None,
                required=False
                )    
    except:
        pass

    start = forms.DateField(label=_("Date of Inspection Start"), required=False)
    end = forms.DateField(label=_("Date of Inspection End"), required=False)    

    def __init__(self, *args, **kwargs):
        super(InspectionFilterForm, self).__init__(*args, **kwargs)
        self.fields['start'].widget.attrs['class'] ="calenda"
        self.fields['end'].widget.attrs['class'] ="calenda"

        self.fields['owner'] = forms.ChoiceField(
            label=_('Owner'),
            required=False,
            initial = None,
            widget=forms.Select(),
            choices=get_user_choice_list() )
        

from django.contrib.auth import get_user_model
UserModel = get_user_model()
 

class DashboardForm(forms.Form):
    year = forms.IntegerField(
        label=_('year'),
        initial=timezone.now().year,
        min_value=2000,
        required=False)    

    def clean_year(self):
        year = self.cleaned_data['year']
        if year:
            raise forms.ValidationError(_('This field is required.')) 

        return year

    def __init__(self, *args, **kwargs):
        super(DashboardForm, self).__init__(*args, **kwargs)
        self.fields['year'].widget.attrs['class'] ="form-control"
        self.fields['year'].widget.attrs['min'] ="2000"
        self.fields['year'].widget.attrs['max'] = timezone.now().year + 1        
