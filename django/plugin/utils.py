import os
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import FileField
from django.core.cache import cache
from django.conf import settings
from django.utils.translation import ugettext_lazy as _




def file_cleanup(sender, **kwargs):
    """
    File cleanup callback used to emulate the old delete
    behavior using signals. Initially django deleted linked
    files when an object containing a File/ImageField was deleted.

    Usage:
    >>> from django.db.models.signals import post_delete
    >>> post_delete.connect(file_cleanup, sender=MyModel, dispatch_uid="mymodel.file_cleanup")
    """
    # for fieldname in sender._meta.get_all_field_names():
    for fieldname in sender._meta.fields:
        try:
            field = sender._meta.get_field(fieldname)
        except:
            field = None
        if field and isinstance(field, FileField):
            inst = kwargs['instance']
            f = getattr(inst, fieldname)
            m = inst.__class__._default_manager
            if hasattr(f, 'path') and os.path.exists(f.path)\
            and not m.filter(**{'%s__exact' % fieldname: getattr(inst, fieldname)})\
            .exclude(pk=inst._get_pk_val()):
                try:
                    if settings.USE_SAE_BUCKET: #'SERVER_SOFTWARE' in os.environ: 
                        from sae import storage
                        from saewrapper.storage.bucket import SAEBucket
                        raise RuntimeError('env setup' % f.path)
                        SAEBucket().delete(f.path)
                    else:
                        default_storage.delete(f.path)
                except:
                    pass

            if hasattr(f, 'thumb_path') and os.path.exists(f.thumb_path)\
            and not m.filter(**{'%s__exact' % fieldname: getattr(inst, fieldname)})\
            .exclude(pk=inst._get_pk_val()):
                try:
                    if settings.USE_SAE_BUCKET: #'SERVER_SOFTWARE' in os.environ: 
                        from sae import storage
                        from saewrapper.storage.bucket import SAEBucket
                        raise RuntimeError('env setup' % f.thumb_path)
                        SAEBucket().delete(f.thumb_path)
                    else:
                        default_storage.delete(f.thumb_path)
                except:
                    pass
                    
def file_cleanup2(sender, **kwargs):
    inst = kwargs['instance']
    try:
        cache_key = ("%s %d") % (inst.__class__.__name__ , inst._get_pk_val())
        inst_raw = cache.get(cache_key)
    except:
        return

    if settings.USE_SAE_BUCKET: # 'SERVER_SOFTWARE' in os.environ: 
        from sae import storage
        from saewrapper.storage.bucket import SAEBucket
        pass

    # for fieldname in sender._meta.get_all_field_names():
    for fieldname in sender._meta.fields:
        try:
            field = sender._meta.get_field(fieldname)
        except:
            field = None
        if field and isinstance(field, FileField):            
            if (not inst_raw is None) and (inst_raw.__class__.__name__ == inst.__class__.__name__):
                f = getattr(inst_raw, fieldname)
                m = inst_raw.__class__._default_manager
                path = None
                
                # check file exist
                if settings.USE_SAE_BUCKET: #'SERVER_SOFTWARE' in os.environ:                     
                    path = SAEBucket().url(f.name)
                    if not path:
                        continue
                else:
                    if not (hasattr(f, 'path') and os.path.exists(f.path)):
                        continue
                
                # check whether file changed
                if getattr(inst_raw, fieldname) == getattr(inst, fieldname):                    
                    continue                
                
                # check whether exact same instance
                if not m.filter(**{'%s__exact' % fieldname: getattr(inst_raw, fieldname)})\
                .exclude(pk=inst_raw._get_pk_val()):
                    try:
                        if settings.USE_SAE_BUCKET: #'SERVER_SOFTWARE' in os.environ:                            
                            SAEBucket().delete(f.name)
                        else:
                            default_storage.delete(f.path)
                    except:
                        pass       
    cache.delete(cache_key)
    
def save_raw_instance(sender, instance, *args, **kwargs):
    try:
        pk = instance._get_pk_val()
        inst = instance.__class__._default_manager.get(pk=pk)
        cache_key = ("%s %d") % (inst.__class__.__name__ , inst._get_pk_val())
        cache.set(cache_key, inst)                           
    except:
        pass

from django.db.models import fields

from django import forms
class PercentageDigitField(fields.FloatField):
    widget = forms.TextInput(attrs={"class": "percentInput"})

    def to_python(self, value):
        val = super(PercentageField, self).to_python(value)
        if is_number(val):
            return val/100
        return val

    def prepare_value(self, value):
        val = super(PercentageField, self).prepare_value(value)
        if is_number(val) and not isinstance(val, str):
            return str((float(val)*100))
        return val

def is_number(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False

from django.core.exceptions import ValidationError
# accepted 50%, 50 = 50%

def valid_percentage(val):
    val2 = val
    if val.endswith("%"):
        val2 = val[:-1] #remove last "$"
    try:
        return float(val2)
    except ValueError:
        raise ValidationError(
            _('%(value)s is not a valid percentage'),
              params={'value': val},
       )     

class PercentageField(fields.CharField):
    def validate(self, value, model_instance):
        #return super(PercentageField, self).validators + valid_percentage
        return valid_percentage(value)

    # cover before handled by backend
    def to_python(self, value):
        val = super(PercentageField, self).to_python(value)
        if val and not val.endswith("%"):
            return val + "%"        
        return val

    def prepare_value(self, value):
        val = super(PercentageField, self).prepare_value(value)
        if not val.endswith("%"):
            return val + "%"
        return val

def get_exist_option_items(options, queryset, fieldname):
    exist_in_qs = [getattr(_,fieldname) for _ in queryset]
    exist_matched = [_ for _ in options if _[0] in exist_in_qs]
    return exist_matched

from django.http import HttpResponse, HttpResponseRedirect
import csv
import codecs
from django.utils.encoding import force_str, force_text

def gen_csv(model, qs, filename, fields_display, fields_fk, fields_datetime, excludes, fields_multiple=None, fields_property=None):
        response = HttpResponse(content_type='text/csv')        
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        response.write(codecs.BOM_UTF8) # add bom header
        writer = csv.writer(response)

        row = []
        # fields_display = [ "use_condition", ]
        # fields_fk = ["equipment",  ]
        # fields_datetime = ["updated","completed_time", ]
        for field in model._meta.get_fields():
            if field.name in excludes:
                continue
            row.append(field.verbose_name)

        if fields_property:
            for field in fields_property:
                row.append(_(field[1]))            
        writer.writerow(row)

        for obj in qs:
            row = []
            for field in model._meta.get_fields():
                if field.name in excludes:
                    continue
                    
                #row.append(field.value_to_string(obj).encode('utf8'))
                value = getattr(obj, field.name) 
                if value:
                    if field.name in fields_datetime:
                        if isinstance(field, models.DateTimeField):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            value = value.strftime('%Y-%m-%d')                        
                    elif field.name in fields_display:
                        value = obj._get_FIELD_display(field)
                    elif field.name in fields_fk:
                        value = force_text(value, strings_only=True)
                    elif fields_multiple and field.name in fields_multiple:
                        str = "{0}{1}()".format("obj.get_",field.name)
                        value = eval(str)
                    value = "%s" %  (value)
                    if fields_multiple and field.name in fields_multiple:
                        row.append(value)
                    else:
                        row.append(value.encode('utf8'))
                else:
                    row.append("")

            if fields_property:
                for field in fields_property:
                    value = getattr(obj, field[0]) 
                    row.append(value)
                    
            writer.writerow(row)    

        return response

def gen_csv_file(model, qs, filename, fields_display, fields_fk, fields_datetime, excludes, fields_multiple=None):

    import csv
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')

        csvfile.write(codecs.BOM_UTF8)   
        
        row = []
        # fields_display = [ "use_condition", ]
        # fields_fk = ["equipment",  ]
        # fields_datetime = ["updated","completed_time", ]
        for field in model._meta.get_fields():
            if field.name in excludes:
                continue
            row.append(field.verbose_name)
        writer.writerow(row)

        for obj in qs:
            row = []
            for field in model._meta.get_fields():
                if field.name in excludes:
                    continue
                    
                #row.append(field.value_to_string(obj).encode('utf8'))
                value = getattr(obj, field.name) 
                if value:
                    if field.name in fields_datetime:
                        if isinstance(field, models.DateTimeField):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            value = value.strftime('%Y-%m-%d')                        
                    elif field.name in fields_display:
                        value = obj._get_FIELD_display(field)
                    elif field.name in fields_fk:
                        value = force_text(value, strings_only=True)
                    elif fields_multiple and field.name in fields_multiple:
                        str = "{0}{1}()".format("obj.get_",field.name)
                        value = eval(str)
                    value = "%s" %  (value)
                    if fields_multiple and field.name in fields_multiple:
                        row.append(value)
                    else:
                        row.append(value.encode('utf8'))
                else:
                    row.append("")
            writer.writerow(row)    
        
