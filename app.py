# -*- coding: utf-8 -*-
import os
import logging
import psycopg2
import datetime
from contextlib import closing
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from pyramid.events import NewRequest, subscriber
from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from waitress import serve
from cryptacular.bcrypt import BCRYPTPasswordManager


# "Use the __file__ global special attribute to get the Python object
# corresponding to the current code file." -- Cris
here = os.path.dirname(os.path.abspath(__file__))

TABLE1_SCHEMA = """
CREATE TABLE IF NOT EXISTS days (
    date DATE PRIMARY KEY,
    dow SMALLINT NOT NULL)
"""
TABLE2_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id serial PRIMARY KEY,
    r_id INTEGER NOT NULL,
    repeats BOOLEAN NOT NULL,
    description TEXT NOT NULL,
    date DATE REFERENCES days(date) NOT NULL,
    time TIME NOT NULL,
    time_end TIME NOT NULL)
"""

SEQUECE_SCHEMA = """
CREATE SEQUENCE rid NO MAXVALUE OWNED BY events.r_id
"""

ADD_EVENT = """
INSERT INTO events (repeats, r_id, description, date, time, time_end) VALUES (%s, %s, %s, %s, %s, %s)
"""

REMOVE_EVENT = """
DELETE FROM events WHERE id=%s
"""

REMOVE_EACH_EVENT = """
DELETE FROM events WHERE r_id=%s
"""

RETRIEVE_DAY = """
SELECT time, time_end, description, r_id, id, repeats from events WHERE date=%s ORDER BY time ASC
"""

logging.basicConfig()
log = logging.getLogger(__file__)


def convert_to_readable_format(date):
    """converts a date's format from YYYY-MM-DD to <Month> <Day>, <Year>"""
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
    'September', 'October', 'November', 'December']
    year = date.split('-')[0]
    month_int = int(date.split('-')[1].lstrip('0'))
    month = months[month_int - 1]
    day = date.split('-')[2].lstrip('0')
    if day[-1] == '1':
        day += 'th' if day == '11' else 'st'
    elif day[-1] == '2':
        day += 'nd'
    elif day[-1] == '3':
        day += 'rd'
    else:
        day += 'th'
    return '{m} {d}, {y}'.format(y=year, m=month, d=day)


@view_config(route_name='calendar', renderer='templates/calendar.jinja2')
def read_calendar(request):

    class Month(object):
        def __init__(self, name, num):
            self.name = name
            self.num = num

    January = Month("January", 1)
    February = Month("February", 2)
    March = Month("March", 3)
    April = Month("April", 4)
    May = Month("May", 5)
    June = Month("June", 6)
    July = Month("July", 7)
    August = Month("August", 8)
    September = Month("September", 9)
    October = Month("October", 10)
    November = Month("November", 11)
    December = Month("December", 12)

    calendar = [January, February, March, April, May, June, July, August, September, October, November, December]
    return {'calendar': calendar}


@view_config(route_name='calendar_month', renderer='templates/calendar_month.jinja2')
def read_calendar_month(request):
    the_month = int(request.params['month'])
    prev_month = 12 if the_month == 1 else the_month - 1
    next_month = 1 if the_month == 12 else the_month + 1
    # Need to get the year from request.params too
    # For now, this year:
    the_year = datetime.date.today().year
    first_of_month = datetime.date(the_year, the_month, 1)
    # Grab the strfied month:
    month_name = first_of_month.strftime('%B')
    cur = request.db.cursor()
    cur.execute("SELECT dow FROM days WHERE date=%s", [first_of_month])
    query_result = cur.fetchall()
    dow = query_result[0][0]
    # Grab the first Sunday on or before the 1st of the month:
    first_sunday = first_of_month - datetime.timedelta(dow)
    last_saturday = first_sunday + datetime.timedelta(41)
    cur.execute("SELECT date FROM days WHERE date >= %s AND date <= %s", [first_sunday, last_saturday])
    query_result = cur.fetchall()
    # Format results as list of date objects
    dates = [result[0] for result in query_result]
    if the_month == 1:
        dow = dates[0].isoweekday() if dates[0].isoweekday() != 7 else 0
        front = [0] * dow # Shouldn't matter what goes here. Just the length of the list is important.
        dates = front + dates
    return {'dates': dates, 'month_name': month_name, 'the_month': the_month,
    'prev_month': prev_month, 'next_month': next_month}


@view_config(route_name='date', renderer='templates/date.jinja2')
def read_date(request):
    date = str(request.params['date'])
    readable_date = convert_to_readable_format(date)
    cur = request.db.cursor()
    cur.execute(RETRIEVE_DAY, [date])
    query_result = cur.fetchall()
    result = [(tup[0].strftime('%I:%M %p').lstrip('0'), tup[1].strftime('%I:%M %p').lstrip('0'), str(tup[2]), tup[3], tup[4], tup[5]) for tup in query_result]

    class Event(object):
        def __init__(self, i_d, r_id, repeats, start_time, end_time, description):
            self.id = i_d
            self.r_id = r_id
            self.repeats = repeats
            self.time = start_time
            self.time_end = end_time
            self.description = description

    events = []
    # For each event in results, event[0] is start time, event[1] is end time, event[2] is description, event[3] is repeat_id, event[4] is id,
    # event[5] is repeats
    for event in result:
        events.append(Event(event[4], event[3], event[5], event[0], event[1], event[2]))

    return {'date': date, 'readable_date': readable_date, 'events': events}


@view_config(route_name='home', renderer='templates/day.jinja2')
def read_day(request):
    # We want the main view page to always display today's events
    # This will be for viewing only.
    today = str(datetime.datetime.today()).split(' ')[0]
    cur = request.db.cursor()
    cur.execute(RETRIEVE_DAY, [today])
    query_result = cur.fetchall()
    result = [(tup[0].strftime('%I:%M %p').lstrip('0'), tup[1].strftime('%I:%M %p').lstrip('0'), str(tup[2])) for tup in query_result]

    # Our view function needs to return the packaged information we've requested in a format
    # that our jinja2 template can render.

    return {'today': convert_to_readable_format(today), 'events': result}


def delete_event(request):
    """removes an event from the calendar"""
    del_all = bool(request.params['del_all']) # Apparently I can only pass strings through HTML forms
    if del_all:
        event_id = request.params['r_id']
        request.db.cursor().execute(REMOVE_EACH_EVENT, [event_id])
    else:
        event_id = request.params['id']
        request.db.cursor().execute(REMOVE_EVENT, [event_id])


@view_config(route_name='delete', request_method='POST')
def delete_event_view(request):
    """view function to remove an event from the calendar"""
    try:
        delete_event(request)
    except psycopg2.Error as e:
        return HTTPInternalServerError

    date = request.params['date']
    route = '/date?date={date}'.format(date=date)
    return HTTPFound(route)


def get_next_rid(request):
    cursor = request.db.cursor()
    cursor.execute("SELECT NEXTVAL('rid')")
    results = cursor.fetchone()
    # results = (####L,)
    return int(results[0])


def add_event(request):
    """adds an event to the calendar"""
    repeat_id = get_next_rid(request)
    final_date = datetime.date(datetime.date.today().year, 12, 31)
    repeat = request.params['repeat']
    event = request.params['description']
    date = request.params['date']
    time = request.params['time']
    time_end = request.params['time_end']
    date_nums = date.split('-')
    current = datetime.date(int(date_nums[0]), int(date_nums[1]), int(date_nums[2]))
    if time_end < time:
        raise ValueError('End time must be later than start time')
    repeats = 't'
    if repeat == 'never':
        repeats = 'f'
        request.db.cursor().execute(ADD_EVENT, [repeats, repeat_id, event, date, time, time_end])
    elif repeat == 'monthly':
        the_day = int(date_nums[2])
        current_month = int(date_nums[1])
        while current_month <= 12:
            date = datetime.date(int(date_nums[0]), current_month, the_day)
            request.db.cursor().execute(ADD_EVENT, [repeats, repeat_id, event, date, time, time_end])
            current_month += 1
    else:
        if repeat == 'daily':
            f = 1
        elif repeat == 'weekly':
            f = 7
        elif repeat == 'biweekly':
            f = 14
        while current <= final_date:
            try:
                request.db.cursor().execute(ADD_EVENT, [repeats, repeat_id, event, current, time, time_end])
            except psycopg2.Error:
                break;
            else:
                current += datetime.timedelta(f)


@view_config(route_name='add', request_method='POST')
def add_event_view(request):
    """view function to add an event to the calendar"""
    try:
        add_event(request)
    except psycopg2.Error as e:
        return HTTPInternalServerError
    # Since the URL named 'date' requires form information to render,
    # we cannot simply return HTTPFound(request.route_url('date')).
    # The form information we need is appended to the URL in the form of
    # "?date=<some date>". We can grab this information from the request object
    # and return a route suitable for HTTPFound() with everything we need.
    date = request.params['date']
    route = '/date?date={date}'.format(date=date)
    return HTTPFound(route)


def connect_db(settings):
    return psycopg2.connect(settings['db'])


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password required')
    settings = request.registry.settings
    manager = BCRYPTPasswordManager()
    if username == os.environ.get('auth.username', ''):
        hased = settings.get('auth.password', '')
        return manager.check(hashed, password)


def init_db():
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=calendar_db user=store'
    )
    with closing(connect_db(settings)) as db:
        db.cursor().execute(TABLE1_SCHEMA)
        db.cursor().execute(TABLE2_SCHEMA)
        db.cursor().execute(SEQUECE_SCHEMA)
        db.commit()

    def populate_calendar():
        INSERT_DAY = """
        INSERT INTO days (date, dow) VALUES (%s, %s)
        """
        # I am starting the database on Jan 1st of the current year.
        # I will need to update this for the next year if this project turns out.
        date = datetime.date(2015, 1, 1)
        dow = (date.weekday() + 1) % 7  # <- Sunday: 0, Monday : 1, ..., Saturday: 6
        with closing(connect_db(settings)) as db:
            for i in xrange(365):
                db.cursor().execute(INSERT_DAY, [date, dow])
                date += datetime.timedelta(1)
                dow = (date.weekday() + 1) % 7
            db.commit()

    populate_calendar()


@subscriber(NewRequest)
def open_connection(event):
    # The event object has access to to the newly created request, your app,
    # settings, etc.
    request = event.request
    settings = request.registry.settings
    # Now we hang our database connection on the request object
    request.db = connect_db(settings)
    request.add_finished_callback(close_connection)


def close_connection(request):
    """close the database connection for this request

    If there has been an error in the processing of the request, abort any open
    transactions.
    """
    db = getattr(request, 'db', None)
    if db is not None:
        if request.exception is not None:
            db.rollback()
        else:
            db.commit()
        request.db.close()


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=calendar_db user=store'
    )
    settings['auth.username'] = os.environ.get('AUTH_USERNAME', 'admin')
    manager = BCRYPTPasswordManager()
    settings['auth.password'] = os.environ.get(
        'AUTH_PASSWORD', manager.encode('sneakysecret'))
    # secret value for session signing:
    secret = os.environ.get('CALENDAR_SESSION_SECRET', 'supersecret')
    session_factory = SignedCookieSessionFactory(secret)
    auth_secret = os.environ.get('CALENDAR_AUTH_SECRET', 'superdupersecret')
    # configuration setup
    config = Configurator(
        settings=settings,
        session_factory=session_factory,
        authentication_policy=AuthTktAuthenticationPolicy(secret=auth_secret, hashalg='sha512'),
        authorization_policy=ACLAuthorizationPolicy(),
    )
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.add_route('home', '/')
    config.add_route('add', '/add')
    config.add_route('delete', '/delete')
    config.add_route('date', '/date')
    config.add_route('calendar', '/calendar')
    config.add_route('calendar_month', '/calendar_month')
    config.scan()
    app = config.make_wsgi_app()
    return app

if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
