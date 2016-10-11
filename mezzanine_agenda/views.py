from __future__ import unicode_literals
from future.builtins import str
from future.builtins import int
from calendar import month_name, day_name

from datetime import datetime, date, timedelta

from django.contrib.sites.models import Site
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
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


def event_list(request, tag=None, year=None, month=None, day=None, username=None,
                   location=None, week=None, template="agenda/event_list.html"):
    """
    Display a list of events that are filtered by tag, year, month, week,
    author or location. Custom templates are checked for using the name
    ``agenda/event_list_XXX.html`` where ``XXX`` is either the
    location slug or author's username if given.
    """
    settings.use_editable()
    templates = []
    day_date = None
    events = Event.objects.published(for_user=request.user)

    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        events = events.filter(keywords__keyword=tag)
    else:
        for exclude_tag_slug in settings.EVENT_EXCLUDE_TAG_LIST:
            exclude_tag = get_object_or_404(Keyword, slug=exclude_tag_slug)
            events = events.exclude(keywords__keyword=exclude_tag)

    # if not day:
    #     events = events.filter(parent=None)
    if year is not None:
        events = events.filter(start__year=year)
        if month is not None:
            events = events.filter(start__month=month)
            try:
                month_orig = month
                month = month_name[int(month)]
            except IndexError:
                raise Http404()
            if day is not None:
                events = events.filter(start__day=day)
                day_date = date(year=int(year), month=int(month_orig), day=int(day))
        elif week is not None:
            events = events.filter(start__year=year)
            lower_date, higher_date = week_day_range(year, week)
            events = events.filter(start__range=(lower_date, higher_date))
    else:
        year = events[0].start.year
    if location is not None:
        location = get_object_or_404(EventLocation, slug=location)
        events = events.filter(location=location)
        templates.append(u"agenda/event_list_%s.html" %
                          str(location.slug))
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        events = events.filter(user=author)
        templates.append(u"agenda/event_list_%s.html" % username)
    if not tag and not year and not location and not username:
        #Get upcoming events/ongoing events
        events = events.filter(Q(start__gt=datetime.now()) | Q(end__gt=datetime.now())).order_by("start")

    prefetch = ("keywords__keyword",)
    events = events.select_related("user").prefetch_related(*prefetch)
    events = paginate(events, request.GET.get("page", 1),
                          settings.EVENT_PER_PAGE,
                          settings.MAX_PAGING_LINKS)
    context = {"events": events, "year": year, "month": month, "day": day, "week": week,
               "tag": tag, "location": location, "author": author, 'day_date':day_date}
    templates.append(template)
    return render(request, templates, context)


def event_detail(request, slug, year=None, month=None, day=None,
                     template="agenda/event_detail.html"):
    """. Custom templates are checked for using the name
    ``agenda/event_detail_XXX.html`` where ``XXX`` is the agenda
    events's slug.
    """
    events = Event.objects.published(for_user=request.user).select_related()
    event = get_object_or_404(events, slug=slug)
    if event.parent:
        context_event = event.parent
        context_event.sub_title = event.sub_title
        context_event.start = event.start
        context_event.end = event.end
        context_event.location = event.location
        child = event
    else:
        context_event = event
        child = None
    context = {"event": context_event, "child": child, "editable_obj": event}
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
    context = {"event": event, "editable_obj": event, "shop_url": settings.EVENT_SHOP_URL}
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
