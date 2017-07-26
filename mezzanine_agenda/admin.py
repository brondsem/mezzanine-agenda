from __future__ import unicode_literals

from copy import deepcopy

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from mezzanine_agenda.models import Event, EventLocation, EventPrice, EventCategory, EventShop, Season
from mezzanine.conf import settings
from mezzanine.core.admin import DisplayableAdmin, OwnableAdmin



class EventAdminBase(admin.ModelAdmin):

    model = Event


class EventAdmin(DisplayableAdmin, OwnableAdmin):
    """
    Admin class for events.
    """

    fieldsets = deepcopy(EventAdminBase.fieldsets)
    exclude = ("short_url", )
    list_display = ["title", "start", "end", "user", "rank", "status", "admin_link"]
    if settings.EVENT_USE_FEATURED_IMAGE:
        list_display.insert(0, "admin_thumb")
    list_filter = deepcopy(DisplayableAdmin.list_filter) + ("location",)
    ordering = ('-start',)

    def save_form(self, request, form, change):
        """
        Super class ordering is important here - user must get saved first.
        """
        OwnableAdmin.save_form(self, request, form, change)
        return DisplayableAdmin.save_form(self, request, form, change)


class EventLocationAdmin(admin.ModelAdmin):
    """
    Admin class for event locations. Hides itself from the admin menu
    unless explicitly specified.
    """

    fieldsets = ((None, {"fields": ("title", "address", "postal_code", "city", "room", "mappable_location", "lat", "lon", "description", "link" )}),)

    def in_menu(self):
        """
        Hide from the admin menu unless explicitly set in ``ADMIN_MENU_ORDER``.
        """
        for (name, items) in settings.ADMIN_MENU_ORDER:
            if "mezzanine_agenda.EventLocation" in items:
                return True
        return False


class SeasonAdminBase(admin.ModelAdmin):

    list_display = ["title", 'start', 'end']
    model = Season


admin.site.register(Event, EventAdmin)
admin.site.register(EventLocation, EventLocationAdmin)
admin.site.register(EventPrice)
admin.site.register(EventCategory)
admin.site.register(EventShop)
admin.site.register(Season, SeasonAdminBase)
