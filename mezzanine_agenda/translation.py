from modeltranslation.translator import translator, register, TranslationOptions

from mezzanine_agenda.models import Event, EventLocation


@register(Event)
class EventTranslationOptions(TranslationOptions):

    fields = ('title', 'sub_title', 'description', 'content', 'mentions')

@register(EventLocation)
class EventLocationTranslationOptions(TranslationOptions):

    fields = ('description',)
