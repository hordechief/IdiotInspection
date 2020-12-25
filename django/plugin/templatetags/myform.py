from django import template
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe 
#form django.template.defaultfilters import linebreaksbr
from django.template.defaultfilters import capfirst, linebreaksbr

register = template.Library()

def get_model_item(inst, fieldname):
    if not fieldname.find("__") == -1: # only one __ allowed
        modelname, fieldname2 = fieldname.split("__")
        inst = getattr(inst, modelname)
        fieldname = fieldname2
    return inst, fieldname
        
#register.filter('render_field',render_field)
@register.filter(name='render_field')
def render_field(value):
    if value.__len__() > 30:
        return '%s......'% value[0:30]
    else:
        return value


@register.filter(name='my_isboolean')
def my_isboolean(inst, fieldname):
    if hasattr(inst, fieldname):
        field = inst._meta.get_field(fieldname)   
        if isinstance(field, models.BooleanField):
            return True

    return False
    
# field value in db
@register.filter(name='my_get_field_value')
def my_get_field_value(inst, fieldname):
    inst, fieldname = get_model_item(inst, fieldname)
        
    if hasattr(inst, fieldname):
        value = getattr(inst, fieldname)
        if None == value:
            value = ""
        else:
            pass
        return value

    return None

@register.filter(name='my_get_field_value_safe')
def my_get_field_value_safe(inst, fieldname):
    value =  my_get_field_value(inst, fieldname)
    if value:
        # value = mark_safe(value.replace('\n', '<br />'))
        value = linebreaksbr(value)
    return value
    
@register.filter(name='my_get_field_url')
def my_get_field_url(inst, fieldname):
    if hasattr(inst, fieldname):
        value = getattr(inst, fieldname)
        if hasattr(value, "url"):
            return value.url

    return None

@register.filter(name='my_get_foreign_field_url')
def my_get_foreign_field_url(inst, fieldname):
    if hasattr(inst, fieldname):
        object = getattr(inst, fieldname).first()
        if hasattr(object, "image"):
            img = object.image   # this step will fail if the "fieldname" is not "image", hardcoded here!!!! use object.get_image_display_url() to replace late
            if hasattr(img, "url"):
                return img.url
        
    return None
    
@register.filter(name='my_hasattr')
def my_hasattr(inst, fieldname):
    try:
        if hasattr(inst, fieldname):
            return True
    except:
        pass
    return False
    
# field value for display ( options, i18n)
@register.filter(name='my_get_field_display')
def my_get_field_display(inst, fieldname):
    inst, fieldname = get_model_item(inst, fieldname)
        
    if hasattr(inst, fieldname):
        field = inst._meta.get_field(fieldname)   
        value = getattr(inst, fieldname)
        if True == value and my_isboolean(inst, fieldname):
            return  _("Yes")
        elif False == value and my_isboolean(inst, fieldname):
            return  _("No")
        elif None == value:
            return  ""
        else:
            pass
        return "%s" % inst._get_FIELD_display(field)  
        #return inst.my_get_field_display(fieldname)
    return None
    
# field lable / verbose name
@register.filter(name='my_get_field_verbose_name')
def my_get_field_verbose_name(inst, fieldname):
    inst, fieldname = get_model_item(inst, fieldname)
        
    if hasattr(inst, fieldname):
        field = inst._meta.get_field(fieldname)
        return field.verbose_name
    return None

@register.filter(name='my_get_field_css')
def my_get_field_css(ins, fieldname):
    return ins.css(fieldname)

    
@register.filter(name='my_get_pk_name')
def my_get_pk_name(inst):
    meta = inst._meta
    return meta.pk.attname

"""
def get_pk_name(model):
    meta = model._meta.concrete_model._meta
    return _get_pk(meta).name
"""

@register.filter(name='gradient_normal')
def gradient_normal(val):
    if val > -1.5 and val < 1.5:
        return True
    return False

@register.filter(name='list_elem')
def list_elem(list, index):
    if len(list) < index + 1:
        return None
    return list[index]

@register.filter(name='my_get_dict')
def my_get_dict(dict, key):
    if not dict or None==key:
        return None
    return dict.get(key)[0]


@register.filter(name='get_instance_name')
def get_instance_name(inst):
    if inst:
        return inst.__class__.__name__ 
    return None


def mypaginate(context):
    return context

register.inclusion_tag('includes/pagination.html', takes_context=True)(mypaginate)


@register.filter(name='distribution_status')
def distribution_status(ins, obj):
    return _(ins.distribution_status(obj))

@register.filter(name='distribution_quantity')
def distribution_quantity(ins, obj):
    return ins.distribution_quantity(obj)

    
