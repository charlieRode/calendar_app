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
from waitress import serve


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
    description TEXT NOT NULL,
    date DATE REFERENCES days(date) NOT NULL,
    time TIME NOT NULL)
"""

ADD_EVENT = """
INSERT INTO events (description, date, time) VALUES (%s, %s, %s)
"""

REMOVE_EVENT = """
DELETE FROM events WHERE description=%s
"""

RETRIEVE_DAY = """
SELECT time, description from events WHERE date=%s ORDER BY time ASC
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
        day += 'st'
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
    return {'dates': dates, 'month_name': month_name, 'the_month': the_month,
    'prev_month': prev_month, 'next_month': next_month}


@view_config(route_name='date', renderer='templates/date.jinja2')
def read_date(request):
    date = str(request.params['date'])
    readable_date = convert_to_readable_format(date)
    cur = request.db.cursor()
    cur.execute(RETRIEVE_DAY, [date])
    query_result = cur.fetchall()
    result = [(tup[0].strftime('%I:%M %p').lstrip('0'), str(tup[1])) for tup in query_result]
    return {'date': date, 'readable_date': readable_date, 'events': result}


@view_config(route_name='home', renderer='templates/day.jinja2')
def read_day(request):
    # We want the main view page to always display today's events
    # This will be for viewing only.
    today = str(datetime.datetime.today()).split(' ')[0]
    cur = request.db.cursor()
    cur.execute(RETRIEVE_DAY, [today])
    query_result = cur.fetchall()
    result = []
    # Convert all elements in the returned list of tuples to strings
    for tup in query_result:
        result.append( (tup[0].strftime('%I:%M %p').lstrip('0'), str(tup[1])) )
    # Our view function needs to return the packaged information we've requested in a format
    # that our jinja2 template can render. This format is a dictionary, whose keys are strings
    # that are referenced in the template.

    return {'today': convert_to_readable_format(today), 'events': dict(result)}


def delete_event(request):
    """removes an event from the calendar"""
    event = request.params['description']
    request.db.cursor().execute(REMOVE_EVENT, [event])


@view_config(route_name='delete', request_method='POST')
def delete_event_view(request):
    """view function to remove an event from the calendar"""
    try:
        delete_event(request)
    except psycopg2.Error:
        return HTTPInternalServerError

    date = request.params['date']
    route = '/date?date={date}'.format(date=date)
    return HTTPFound(route)


def add_event(request):
    """adds an event to the calendar"""
    event = request.params['description']
    date = request.params['date']
    time = request.params['time']
    request.db.cursor().execute(ADD_EVENT, [event, date, time])


@view_config(route_name='add', request_method='POST')
def add_event_view(request):
    """view function to add an event to the calendar"""
    try:
        add_event(request)
    except psycopg2.Error:
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


def init_db():
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=calendar_db user=store'
    )
    with closing(connect_db(settings)) as db:
        db.cursor().execute(TABLE1_SCHEMA)
        db.cursor().execute(TABLE2_SCHEMA)
        db.commit()

    def populate_calendar():
        INSERT_DAY = """
        INSERT INTO days (date, dow) VALUES (%s, %s)
        """
        date = datetime.date.today()
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
    # secret value for session signing:
    secret = os.environ.get('CALENDAR_SESSION_SECRET', 'secret')
    session_factory = SignedCookieSessionFactory(secret)
    # configuration setup
    config = Configurator(
        settings=settings,
        session_factory=session_factory
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
