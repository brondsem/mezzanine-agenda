from mezzanine_agenda.models import Event
import pandas as pd
from pprint import pprint
from collections import OrderedDict

def get_events_list_days_form():
    events = Event.objects.published().order_by('start')
    events_all_date = {}
    events_by_day = []
    day_dict = OrderedDict()

    for event in events:
        events_all_date[event.start.strftime('%Y-%m-%d')] = event.start
        for period in event.periods.all():
            events_all_date[period.date_from.strftime('%Y-%m-%d')] = period.date_from

    day_list = pd.date_range(events_all_date[min(events_all_date)], events_all_date[max(events_all_date)]).tolist()
    for a_day in day_list :
        day_dict[a_day.strftime('%Y-%m-%d')] = a_day.date()

    for day_k, day_v in day_dict.items():
        disabled = ''
        if not day_k in events_all_date.keys():
            disabled = 'disabled'
        events_by_day.append((day_k, {'label': str(day_v.day), 'disabled': disabled}))
    return events_by_day
