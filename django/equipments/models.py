from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta


# Create your models here.a

class EquipmentType(models.Model):
    name = models.CharField(_('Name'), max_length=30, blank=False, null=False)

    class Meta:
        verbose_name = _('Equipment Type')
        verbose_name_plural = _('Equipment Type')

    def __unicode__(self):
        return "%s" % (self.name)

class Equipment(models.Model):
    name = models.CharField(_('Name'), max_length=30, blank=False, null=False) 
    type = models.ForeignKey(EquipmentType,on_delete=models.CASCADE,verbose_name = _('Type'))

    class Meta:
        verbose_name = _('Equipment')
        verbose_name_plural = _('Equipment')

    def __unicode__(self):
        return "%s" % (self.name) 

class AbstractEquipmentInspection(models.Model):
    equipment_use_condition = [
        ('normal', _('Normal')),
        ('breakdown', _('Breakdown')),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, verbose_name=_('Equipment'))
    use_condition = models.CharField(_('Use Condition'), choices=equipment_use_condition, max_length=30, blank=False,null=False,default='normal')
    inspector = models.CharField(_('Inspector'), max_length=30, blank=False,null=False)
    owner = models.CharField(_('Owner'), max_length=30, blank=True, null=True)
    comments = models.TextField(_('Comments'), max_length=130, blank=True, null=True)   
    check_date = models.DateField(_('Date of Inspection'), auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(_('Latest Update'),auto_now_add=False, auto_now=True)
    due_date = models.DateField(_('Due Date'), auto_now_add=False, auto_now=False, null=True, blank=True)
    completed_time = models.DateTimeField(_('rectification completed time'), auto_now_add=False, auto_now=False, null=True, blank=True)

    class Meta:
        verbose_name = _('Equipment Inspection')
        verbose_name_plural = _('Equipment Inspection')
        abstract = True
        unique_together = (('equipment','inspector','check_date'),)

    def get_absolute_url(self):
        return reverse("equipmentinsepction_detail", kwargs={"pk": self.id})    

    def get_use_condition(self):
        return _('Normal') if self.use_condition == 'normal' else _('Breakdown')

    def time_consuming(self):
        return (self.updated.replace(tzinfo=None) - datetime.strptime(str(self.check_date),'%Y-%m-%d').replace(tzinfo=None)).days + 1

        
class EquipmentInspectionManager(models.Manager):
    def get_query_set(self):
        return models.query.QuerySet(self.model, using=self._db)

    def get_this_day(self):
        start = timezone.now().date()
        end = start + timedelta(days=1)

        return self.get_query_set().filter(check_date__range=(start, end))


class EquipmentInspection(AbstractEquipmentInspection):
    objects = EquipmentInspectionManager()

    class Meta:
        abstract = False
        verbose_name = _('Equipment Inspection')
        verbose_name_plural = _('Equipment Inspection')
        
    def __unicode__(self):
        return "%s" % (self.equipment.name)    
