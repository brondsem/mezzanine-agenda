from __future__ import unicode_literals
from future.builtins import str
from future.builtins import int
from calendar import month_name, day_name, monthrange

from datetime import datetime, date, timedelta

from django.contrib.sites.models import Site
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import *
from django.views.generic.base import *

from icalendar import Calendar

from mezzanine_agenda import __version__
from mezzanine_agenda.models import Event, EventLocation
from mezzanine_agenda.feeds import EventsRSS, EventsAtom
from mezzanine.conf import settings
from mezzanine.generic.models import Keyword
from mezzanine.pages.models import Page
from mezzanine.utils.views import render, paginate
from mezzanine.utils.models import get_user_model
from mezzanine.utils.sites import current_site_id

User = get_user_model()


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)

def week_day_range(year, week):
    first_day = date(int(year),1,1)
    lower_date = next_weekday(first_day, 0) + timedelta(weeks=int(week)-1)
    higher_date = lower_date + timedelta(days=int(6))
    return lower_date, higher_date


class EventListView(ListView):
    """
    Display a list of events that are filtered by tag, year, month, week,
    author or location. Custom templates are checked for using the name
    ``agenda/event_list_XXX.html`` where ``XXX`` is either the
    location slug or author's username if given.
    """
    model = Event
    template_name = "agenda/event_list.html"
    context_object_name = 'events'

    def get_queryset(self, tag=None):
        settings.use_editable()
        self.templates = []
        self.day_date = None
        events = None
        self.tag = None if "tag" not in self.kwargs else self.kwargs['tag']
        self.year = None if "year" not in self.kwargs else self.kwargs['year']
        self.month = None if "month" not in self.kwargs else self.kwargs['month']
        self.day = None if "day" not in self.kwargs else self.kwargs['day']
        self.username = None if "username" not in self.kwargs else self.kwargs['username']
        self.location = None if "location" not in self.kwargs else self.kwargs['location']
        self.week = None if "week" not in self.kwargs else self.kwargs['week']

        # display all events if user belongs to the staff
        if self.request.user.is_staff :
            events = Event.objects.all()
        else :
            events = Event.objects.published(for_user=self.request.user)

        if self.tag is not None:
            self.tag = get_object_or_404(Keyword, slug=self.tag)
            events = events.filter(keywords__keyword=self.tag)
        else:
            for exclude_tag_slug in settings.EVENT_EXCLUDE_TAG_LIST:
                exclude_tag = get_object_or_404(Keyword, slug=exclude_tag_slug)
                events = events.exclude(keywords__keyword=exclude_tag)

        # if not day:
        #     events = events.filter(parent=None)
        if self.year is not None:
            events = events.filter(start__year=self.year)
            if self.month is not None:
                events = events.filter(start__month=self.month)
                try:
                    month_orig = self.month
                    self.month = month_name[int(self.month)]
                except IndexError:
                    raise Http404()
                if self.day is not None:
                    events = events.filter(start__day=self.day)
                    self.day_date = date(year=int(self.year), month=int(month_orig), day=int(self.day))
            elif self.week is not None:
                events = events.filter(start__year=self.year)
                lower_date, higher_date = week_day_range(self.year, self.week)
                events = events.filter(start__range=(lower_date, higher_date))
        if self.location is not None:
            self.location = get_object_or_404(EventLocation, slug=self.location)
            events = events.filter(location=self.location)
            self.templates.append(u"agenda/event_list_%s.html" %
                              str(self.location.slug))
        self.author = None
        if self.username is not None:
            self.author = get_object_or_404(User, username=self.username)
            events = events.filter(user=self.author)
            self.templates.append(u"agenda/event_list_%s.html" % self.username)

        if not self.year and not self.location and not self.username:
            #Get upcoming events/ongoing events
            events = events.filter(Q(start__gt=datetime.now()) | Q(end__gt=datetime.now()))

        prefetch = ("keywords__keyword",)
        events = events.select_related("user").prefetch_related(*prefetch)
        self.templates.append(self.template_name)
        return events

    def get_context_data(self, *args, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        context.update({"year": self.year, "month": self.month, "day": self.day, "week": self.week,
               "tag": self.tag, "location": self.location, "author": self.author, 'day_date': self.day_date})
        if settings.PAST_EVENTS:
            context['past_events'] = Event.objects.filter(end__lt=datetime.now()).order_by("start")
        return context



class ArchiveListView(ListView):
    """
    Display a list of events that are filtered by, year, month, day. Custom templates are checked for using the name
    ``agenda/event_list_XXX.html`` where ``XXX`` is either the
    location slug or author's username if given.
    """
    model = Event
    template_name = "agenda/event_list.html"
    context_object_name = 'events'

    def get_queryset(self, tag=None):

        settings.use_editable()
        self.templates = self.template_name
        self.day_date = None
        events = None
        self.year = None if "year" not in self.kwargs else self.kwargs['year']
        self.month = None if "month" not in self.kwargs else self.kwargs['month']
        self.day = None if "day" not in self.kwargs else self.kwargs['day']

        events = Event.objects.published(for_user=self.request.user)

        if self.year is not None:
            date_now = datetime.now()
            digit_year = int(self.year)
            if date_now.year == digit_year or digit_year == date_now.year - 1:
                date_max = date_now
            else:
                date_max = date(digit_year+1, 7, 31)
            events = events.filter(Q(start__gt=date(int(self.year), 8, 1)), Q(start__lt=date_max)).order_by("-start")

            if self.month is not None:
                digit_month = int(self.month)
                first_day_in_month = date(digit_year, digit_month, 1)
                last_day_in_month = date(digit_year, digit_month,  monthrange(digit_year, digit_month)[1])
                # works for periods containing the month or a period in the month
                events = events.filter((Q(start__lt=first_day_in_month)
                                       & Q(end__gt=last_day_in_month))
                                       | Q(start__range=(first_day_in_month, last_day_in_month))
                                       | Q(end__month=self.month)
                                       | Q(start__month=self.month)).order_by("start")
                try:
                    month_orig = self.month
                    self.month = month_name[int(self.month)]
                except IndexError:
                    raise Http404()
                if self.day is not None:
                    events = events.filter(start__day=self.day)
                    self.day_date = date(year=int(self.year), month=int(month_orig), day=int(self.day))

        events = paginate(events, self.request.GET.get("page", 1),
                              settings.EVENT_PER_PAGE,
                              settings.MAX_PAGING_LINKS)

        return events

    def get_context_data(self, *args, **kwargs):
        context = super(ArchiveListView, self).get_context_data(**kwargs)
        context.update({"year": self.year, "month": self.month, "day": self.day, 'day_date': self.day_date, 'is_archive': True})
        return context


def event_detail(request, slug, year=None, month=None, day=None,
                     template="agenda/event_detail.html"):
    """. Custom templates are checked for using the name
    ``agenda/event_detail_XXX.html`` where ``XXX`` is the agenda
    events's slug.
    """
    events = Event.objects.published(for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)
    context = {"event": event, }
    templates = [u"agenda/event_detail_%s.html" % str(slug), template]
    return render(request, templates, context)


def event_booking(request, slug, year=None, month=None, day=None,
                     template="agenda/event_booking.html"):
    """. Custom templates are checked for using the name
    ``agenda/event_detail_XXX.html`` where ``XXX`` is the agenda
    events's slug.
    """
    events = Event.objects.published(
                                     for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)
    if event.is_full:
        return redirect('event_detail', slug=event.slug)
    shop_url = ''
    if event.external_id:
        if event.shop:
            shop_url = event.shop.item_url % event.external_id
        else:
            shop_url = settings.EVENT_SHOP_URL % event.external_id
    context = {"event": event, "editable_obj": event, "shop_url": shop_url, 'external_id': event.external_id }
    templates = [u"agenda/event_detail_%s.html" % str(slug), template]
    return render(request, templates, context)


def event_feed(request, format, **kwargs):
    """
    Events feeds - maps format to the correct feed view.
    """
    try:
        return {"rss": EventsRSS, "atom": EventsAtom}[format](**kwargs)(request)
    except KeyError:
        raise Http404()


def _make_icalendar():
    """
    Create an icalendar object.
    """
    icalendar = Calendar()
    icalendar.add('prodid',
        '-//mezzanine-agenda//NONSGML V{}//EN'.format(__version__))
    icalendar.add('version', '2.0') # version of the format, not the product!
    return icalendar


def icalendar_event(request, slug, year=None, month=None, day=None):
    """
    Returns the icalendar for a specific event.
    """
    events = Event.objects.published(
                                     for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)

    icalendar = _make_icalendar()
    icalendar_event = event.get_icalendar_event()
    icalendar.add_component(icalendar_event)

    return HttpResponse(icalendar.to_ical(), content_type="text/calendar")


def icalendar(request, tag=None, year=None, month=None, username=None,
                   location=None):
    """
    Returns the icalendar for a group of events that are filtered by tag,
    year, month, author or location.
    """
    settings.use_editable()
    events = Event.objects.published(for_user=request.user)
    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        events = events.filter(keywords__keyword=tag)
    if year is not None:
        events = events.filter(start__year=year)
        if month is not None:
            events = events.filter(start__month=month)
            try:
                month = month_name[int(month)]
            except IndexError:
                raise Http404()
    if location is not None:
        location = get_object_or_404(EventLocation, slug=location)
        events = events.filter(location=location)
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        events = events.filter(user=author)
    if not tag and not year and not location and not username:
        #Get upcoming events/ongoing events
        events = events.filter(Q(start__gt=datetime.now()) | Q(end__gt=datetime.now())).order_by("start")

    prefetch = ("keywords__keyword",)
    events = events.select_related("user").prefetch_related(*prefetch)

    icalendar = _make_icalendar()
    for event in events:
        icalendar_event = event.get_icalendar_event()
        icalendar.add_component(icalendar_event)

    return HttpResponse(icalendar.to_ical(), content_type="text/calendar")


class LocationListView(ListView):

    model = EventLocation
    template_name='agenda/event_location_list.html'

    def get_queryset(self):
        location_list = []
        room = []
        locations = self.model.objects.all().order_by('room')
        for location in locations:
            if location.room:
                if not location.room in room:
                    location_list.append(location)
                    room.append(location.room)
            else:
                location_list.append(location)
        return location_list

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        return context


class LocationDetailView(DetailView):

    model = EventLocation
    template_name='agenda/event_location_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super(LocationDetailView, self).get_context_data(**kwargs)
        return context


class PassView(TemplateView):

    template_name='agenda/event_iframe.html'

    def get_context_data(self, **kwargs):
        context = super(PassView, self).get_context_data(**kwargs)
        context['url'] = settings.EVENT_PASS_URL
        context['title'] = 'Pass'
        return context
