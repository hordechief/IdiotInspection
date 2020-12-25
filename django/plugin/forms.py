from django import forms
from django.forms.widgets import ClearableFileInput, CheckboxInput, Input
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html, html_safe
from django.utils.html import escape    
from django.utils.translation import ugettext_lazy
from django.conf import Settings
import django

# this changed in different django version
class ImageFileInput(ClearableFileInput):
    django_version = django.get_version()
    django_version_big = ".".join(django_version.split(".")[-1])
    if 1.11 > float(django_version_big): # version to be confirmed
        template_with_initial = ('<p class="file-upload">%s</p>'
                                % ClearableFileInput.template_with_initial)
        template_with_clear = ('<span class="clearable-file-input">%s</span>'
                               % ClearableFileInput.template_with_clear)  
    else:
        template_name = 'widgets/clearable_file_input.html'

    # https://stackoverflow.com/questions/27071648/django-imagefield-widget-to-add-thumbnail-with-clearable-checkbox
    def render(self, name, value, attrs=None):
        if 1.11 > float(django.get_version()):
            from django.utils.encoding import force_unicode
            substitutions = {
                'initial_text': self.initial_text,
                'input_text': self.input_text,
                'clear_template': '',
                'clear_checkbox_label': self.clear_checkbox_label,
            }
            template = '%(input)s'
            substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

            if self.is_initial(value):
                template = self.template_with_initial
                substitutions.update(self.get_template_substitution_values(value))
                ### 
                substitutions['initial'] = (
                    '<img src="%s" alt="%s" style="max-width: 200px; max-height: 200px; border-radius: 5px;" /><br/>' % (
                        escape(value.url), escape(force_unicode(value))
                    )
                )
                ###
                if not self.is_required:
                    checkbox_name = self.clear_checkbox_name(name)
                    checkbox_id = self.clear_checkbox_id(checkbox_name)
                    substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                    substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                    substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                    substitutions['clear_template'] = self.template_with_clear % substitutions

            return mark_safe(template % substitutions)
        else:
            return super(ImageFileInput, self).render(name, value, attrs)

    