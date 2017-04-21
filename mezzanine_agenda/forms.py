import ast
from django.forms.widgets import RadioFieldRenderer, RendererMixin, Select, RadioChoiceInput
from django import forms
from mezzanine_agenda.models import *
from mezzanine_agenda.utils import *
from datetime import datetime
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from pprint import pprint


class CustomRadioChoiceInput(RadioChoiceInput):

    def __init__(self, name, value, attrs, choice, index):
        self.name = name
        self.value = value
        self.attrs = attrs
        if choice.__class__.__name__ == 'tuple':
            self.choice_value = force_text(choice[0])
            self.choice_label = force_text(choice[1]['label'])
        self.index = index
        if 'id' in self.attrs:
            self.attrs['id'] += "_%d" % self.index


class CustomRadioFieldRenderer(RadioFieldRenderer):

    choice_input_class = CustomRadioChoiceInput

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id')
        output = []
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = self.__class__(
                    name=self.name,
                    value=self.value,
                    attrs=attrs_plus,
                    choices=choice_label,
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(format_html(self.inner_html, choice_value=choice_value,
                                          sub_widgets=sub_ul_renderer.render()))
            else:
                if "label" in choice_label.keys():
                    if choice_label['disabled']:
                        self.attrs['disabled'] = choice_label['disabled']
                    else :
                        if 'disabled' in self.attrs:
                            del self.attrs['disabled']
                    w = self.choice_input_class(self.name, self.value,
                                                self.attrs.copy(), choice, i)
                    output.append(format_html(self.inner_html,
                                              choice_value=force_text(w), sub_widgets=''))

        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class CustomRadioSelect(RendererMixin, Select):
    renderer = CustomRadioFieldRenderer
    _empty_value = ''


class EventFilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(EventFilterForm, self).__init__(*args, **kwargs)
        event_categories = EventCategory.objects.all()
        event_categories = [(cat.name, cat.name) for cat in event_categories]
        event_locations = EventLocation.objects.distinct('title')
        event_locations = [(loc.title, loc.title) for loc in event_locations]
        events_day = get_events_list_days_form()

        self.fields['event_day_filter'] = forms.ChoiceField(
            required=False,
            widget=CustomRadioSelect,
            choices=events_day,
        )
        self.fields['event_categories_filter'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=event_categories,
        )
        self.fields['event_locations_filter'] = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=event_locations,
        )
