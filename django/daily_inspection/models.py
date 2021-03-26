from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
try:
    from django.core.urls import reverse
except:
    from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.http import Http404
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from uuslug import slugify as uuslugify

from plugin.fields import ThumbnailImageField
from plugin.utils import file_cleanup, file_cleanup2, save_raw_instance

# Create your models here.
'''
class InspectionMixin(models.Model):
    equipment_use_condition = [
        ('normal', _('Normal')),
        ('breakdown', _('Breakdown')),
    ]

    inspector = models.CharField(_('Check Person'), max_length=30, blank=True) 
    owner = models.CharField(_('Owner'), max_length=30, blank=True, null=True)
    due_date = models.DateField(_('Forecast Complete Time'), auto_now_add=False, auto_now=False, null=True, blank=True)
    completed_time = models.DateTimeField(_('rectification completed time'), auto_now_add=False, auto_now=False, null=True, blank=True)    
    check_result = models.CharField(_('Check Result'), choices=equipment_use_condition, max_length=30, blank=True) 
    check_date = models.DateField(_('Check Date'),auto_now_add=True, auto_now=False)

    class Meta:
        abstract=True


RESULT_OPTION = (
    ('yes', 'Yes'),
    ('no', 'No'),
)
'''

def image_upload_to_dailyinspection(instance, filename):
    title, file_extension = filename.split(".")
    #new_filename = "%s-%s.%s" %(instance.created.strftime('%Y-%m-%d-%H-%M-%S'), slugify(title), file_extension)
    if settings.UUSLUGIFY == True:
        new_filename = "%s-%s.%s" %(timezone.now().strftime('%Y%m%d%H%M%S'), uuslugify(title)[:30], file_extension)
    else:
        new_filename = "%s-%s.%s" %(timezone.now().strftime('%Y%m%d%H%M%S'), title, file_extension) # created was not ready for CreateView
    full_filename = "dailyinspection/%s/%s" %(instance.category, new_filename)
    #print(full_filename)
    return full_filename

class DailyInspectionManager(models.Manager):
    def external(self, *args, **kwargs):
        return super(DailyInspectionManager,self).filter(rectification_status__iexact='completed')

    def overdue(self, *args, **kwargs):
        return super(DailyInspectionManager,self).filter(rectification_status__icontains='uncompleted').filter(due_date__lte=timezone.now().date())


class DailyInspection(models.Model):

    daily_insepction_category = (
        ('people', _('People')),
        ('machine', _('Machine')),
        ('device', _('Device')),        
        ('method', _('Method')),
        ('environment', _('Environment')),
    )

    # index can only be 1 char, see SelectMultiple:render & Select(Widget):render_options / selected_choices = set(force_text(v) for v in selected_choices) ==> bug ? set([force_text(v)]
    daily_insepction_impact = (
        ('1', _('economic loss')),
        ('2', _('personnel injury')),
        ('3', _('non-conformance 5SS standard')),
    )

    daily_insepction_correction_status = (
        ('completed', _('Completed')),
        ('uncompleted', _('Uncompleted')),
    )

    daily_insepction_warehouse = (
        ('3', '3#'),
        ('5', '5#'),
    )

    daily_insepction_location = (
        ('1', _('Storage Area')),
        ('2', _('Loading Unloading Area')),
        ('3', _('Vehicle Inspection Area')),
        ('4', _('Office Area')),
        ('5', _('Stock Up Area')),
        ('6', _('Damaged Area')),
        ('7', _('Packing Area')),                                
        ('8', _('Forklift Charging Area')),                                
    )

    daily_insepction_trigger = (
        ('people', 'People'),
        ('ai', 'AI'),
    )
    
    category = models.CharField(_('Category'), max_length=30, choices = daily_insepction_category, blank=False, default = 'device')    
    inspection_content = models.CharField(_('Inspection Content'), max_length=30, blank=False)
    impact = models.CharField(_('Impact'), max_length=30, blank=False)
    rectification_measures = models.TextField(_('Rectification Measures'), max_length=500, blank=False)
    rectification_status = models.CharField(_('Rectification Status'), max_length=30, choices = daily_insepction_correction_status, blank=False, default = 'uncompleted')
    owner = models.CharField(_('Owner'), max_length=30, blank=False)
    inspector = models.ForeignKey(User,verbose_name=_('Inspector'), null=True, blank=True, on_delete=models.CASCADE) 
    due_date = models.DateField(_('Due Date'), auto_now_add=False, auto_now=False)
    created = models.DateTimeField(_('Inspection Created Date'), auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(_('Inspection Updated Date'), auto_now_add=False, auto_now=True)
    completed_time = models.DateTimeField(_('rectification completed time'), auto_now_add=False, auto_now=False, null=True, blank=True)
    image_before = ThumbnailImageField(verbose_name = _('Picture before Rectification'), upload_to=image_upload_to_dailyinspection, blank=False, null=True)
    image_after = models.ImageField(_('Picture after Rectification'), upload_to=image_upload_to_dailyinspection, blank=True, null=True)
    #warehouse = models.CharField(_('Warehouse'), max_length=30, choices = daily_insepction_warehouse, blank=False, default = '3#')
    location = models.CharField(_('Location'), max_length=30, choices = daily_insepction_location, blank=False, default = '1')
    trigger_method = models.CharField(_('trigger method'), max_length=30, choices = daily_insepction_trigger, blank=False, default = 'people')

    objects = DailyInspectionManager()
    
    def __unicode__(self): 
        return _("Daily Inspection") +"-" +  self.inspection_content

    def get_absolute_url(self):
        return reverse("dailyinspection_detail", kwargs={"pk": self.id })    

    def get_absolute_url_update(self):
        return reverse("dailyinspection_update", kwargs={"pk": self.id })    

    def get_absolute_url_delete(self):
        return reverse("dailyinspection_delete", kwargs={"pk": self.id })    


    def get_image_url_before(self):
        img = self.image_before
        if img:
            return img.url
        return img     

    def get_image_url_after(self):
        img = self.image_after
        if img:
            return img.url
        return img 

    def get_html_due_date(self):
        if self.due_date is not None and self.rectification_status == 'uncompleted':
            overdue = ''
            if self.due_date <= timezone.now().date() - timedelta(days=1): # should be 0
                overdue = 'overdue'
            html_text = "<span class='due_date %s'>%s</span>" %(overdue, self.due_date)
        else:
            html_text = "<span class='due_date'></span>"
        return mark_safe(html_text)

    """
    replace by get_xxx_display built-in function

    def get_rectification_status(self):
        return _('Completed') if self.rectification_status == 'completed' else _('Uncompleted')

    def get_location(self):
        for (a,b) in DailyInspection.daily_insepction_location:
            if a == self.location:
                return b
        return None

    def get_category(self):
        for (a,b) in DailyInspection.daily_insepction_category:
            if a == self.category:
                return b
        return None
    """

    def get_impact(self):
        value = ''
        for item in self.impact:
            for (a,b) in DailyInspection.daily_insepction_impact:
                if a == item:
                    if "" == value:
                        value = b
                    else:
                        value = "%s,%s" % (value,b)
                    break
        return value

    def get_created_date(self):
        return self.created.strftime("%Y-%m-%d")

    # can be replaced by field.value_to_string(object)
    def my_get_field_display(self,fieldname):

        if not hasattr(self, fieldname):
            return None
        
        field = DailyInspection._meta.get_field(fieldname)
        return "%s" % self._get_FIELD_display(field)  

    def is_rectification_completed(self)      :
        return self.image_after and hasattr(self.image_after, "url") and self.image_after.url

    def turn_completed(self, instance):
        if self.is_rectification_completed():
            if not instance or not instance.is_rectification_completed():
                return True
        return False

    def rectification_completed_updated(self, instance):
        if self.is_rectification_completed() and instance.is_rectification_completed():
            if not self.image_after.url == instance.image_after.url:
                return True
        return False

    def time_consuming(self):
        return (self.completed_time-self.created).days

    class Meta:
        verbose_name = _("Daily Inspection")
        verbose_name_plural = _("Daily Inspection")
        ordering = ['-created']



post_delete.connect(file_cleanup, sender=DailyInspection, dispatch_uid="DailyInspection.file_cleanup")
post_save.connect(file_cleanup2, sender=DailyInspection, dispatch_uid="DailyInspection.file_cleanup2")
pre_save.connect(save_raw_instance, sender=DailyInspection)

class DailyInspectionLog(models.Model):
    dailyinspection = models.ForeignKey(DailyInspection, verbose_name=_('Daily Inspection'), on_delete=models.CASCADE)
    log = models.CharField(_('log'), max_length=300, blank=False, null=False)

    def __unicode__(self): 
        return ugettext("Daily Inspection") + self.log

