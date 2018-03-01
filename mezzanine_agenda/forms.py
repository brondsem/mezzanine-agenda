import ast
from django.forms.widgets import (RadioFieldRenderer,
                                  RendererMixin,
                                  Select,
                                  RadioChoiceInput,
                                  CheckboxSelectMultiple,
                                  ChoiceFieldRenderer,
                                  CheckboxChoiceInput)
from django import forms
from itertools import chain
from django.utils.translation import ugettext_lazy as _
from mezzanine_agenda.models import *
from mezzanine_agenda.utils import *
from datetime import datetime
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from pprint import pprint
from dal import autocomplete


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

        output.insert(0, "<li>" + str(_(datetime.strptime(self.choices[0][0], '%Y-%m-%d').strftime("%B"))) + "</li>")
        output.insert(len(output) ,  "<li>" + str(_(datetime.strptime(self.choices[len(self.choices) - 1][0], '%Y-%m-%d').strftime("%B"))) + "</li>")
        return format_html(self.outer_html,
                           id_attr=format_html(' id="{}"', id_) if id_ else '',
                           content=mark_safe('\n'.join(output)))


class CustomRadioSelect(RendererMixin, Select):
    renderer = CustomRadioFieldRenderer
    _empty_value = ''


class EventCalendarForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        event_locations = []
        if 'initial' in kwargs:
            if 'event_locations_filter' in kwargs['initial'] :
                event_locations = kwargs['initial']['event_locations_filter']
        events_day = get_events_list_days_form(event_locations)

        self.fields['event_day_filter'] = forms.ChoiceField(
            required=False,
            widget=CustomRadioSelect,
            choices=events_day,
        )

class CustomCheckboxChoiceInput(CheckboxChoiceInput):

    def __init__(self, *args, **kwargs):
        super(CheckboxChoiceInput, self).__init__(*args, **kwargs)
        self.value = set(force_text(v) for v in self.value)
        self.name = self.name + "[]"


class CustomCheckboxFieldRenderer(ChoiceFieldRenderer):

    choice_input_class = CheckboxChoiceInput


class CustomCheckboxFieldRenderer(CustomCheckboxFieldRenderer):
    pass


class CustomCheckboxSelectMultiple(CheckboxSelectMultiple):

    renderer = CustomCheckboxFieldRenderer

    def get_renderer(self, name, value, attrs=None, choices=()):
        """Returns an instance of the renderer."""
        name = name + "[]"
        if value is None:
            value = self._empty_value
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        return self.renderer(name, value, final_attrs, choices)

class EventFilterForm(EventCalendarForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        event_categories = EventCategory.objects.all()
        event_categories = [(cat.name, cat.name) for cat in event_categories]
        event_locations = EventLocation.objects.distinct('title')
        event_locations = [(loc.title, loc.title) for loc in event_locations]

        self.fields['event_categories_filter'] = forms.MultipleChoiceField(
            required=False,
            widget=CustomCheckboxSelectMultiple,
            choices=event_categories,
        )
        self.fields['event_locations_filter'] = forms.MultipleChoiceField(
            required=False,
            widget=CustomCheckboxSelectMultiple,
            choices=event_locations,
        )


class EventAdminForm(forms.ModelForm):

    class Meta:
        model = EventPrice
        fields = ('__all__')
        widgets = {
            'prices': autocomplete.ModelSelect2Multiple(
                url='event-price-autocomplete',
                attrs={'data-html': True}
            )
        }
