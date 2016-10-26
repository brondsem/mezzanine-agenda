from modeltranslation.translator import translator, register, TranslationOptions

from mezzanine_agenda.models import *


@register(Event)
class EventTranslationOptions(TranslationOptions):

    fields = ('title', 'sub_title', 'description', 'content', 'mentions', 'no_price_comments')

@register(EventLocation)
class EventLocationTranslationOptions(TranslationOptions):

    fields = ('description',)

@register(EventCategory)
class EventCategoryTranslationOptions(TranslationOptions):

    fields = ('name', 'description')
