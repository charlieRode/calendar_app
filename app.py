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

RETRIEVE_DAY = """
SELECT time, description from events WHERE date=%s;
"""

logging.basicConfig()
log = logging.getLogger(__file__)


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
    # Reformat
    days = [str(result[0]).split('-')[2].lstrip('0') for result in query_result]
    return {'dates': days, 'month': month_name}



#@view_config(route_name='calendar_month', renderer='templates/calendar_month.jinja2')
#def read_calendar_month(request):
#    month_int = int(request.params['month'])
#    cur = request.db.cursor()
#    cur.execute("SELECT date, dow FROM days")
#    query_result = cur.fetchall()
#    month_starts_on = query_result
#    results = [result[0] for result in query_result]
#    month_name = results[0].strftime('%B')
#    days_of_month = [str(date).split(' ')[0] for date in results if date.month==month_int]
#    days = [day.split('-')[2].lstrip('0') for day in days_of_month]
#    return {'dates': days, 'month': month_name}




#@view_config(route_name='calendar_month', renderer='templates/calendar_month.jinja2')
#def read_calendar_month(request):
#    cur = request.db.cursor()
#    cur.execute("SELECT date FROM days")
#    query_result = cur.fetchall()
#    results = [result[0] for result in query_result]
#    jan = [str(date).split(' ')[0] for date in results if date.month==1]
#    feb = [str(date).split(' ')[0] for date in results if date.month==2]
#    march = [str(date).split(' ')[0] for date in results if date.month==3]
#    april = [str(date).split(' ')[0] for date in results if date.month==4]
#    may = [str(date).split(' ')[0] for date in results if date.month==5]
#    june = [str(date).split(' ')[0] for date in results if date.month==6]
#    july = [str(date).split(' ')[0] for date in results if date.month==7]
#    aug = [str(date).split(' ')[0] for date in results if date.month==8]
#    sept = [str(date).split(' ')[0] for date in results if date.month==9]
#    octb = [str(date).split(' ')[0] for date in results if date.month==10]
#    nov = [str(date).split(' ')[0] for date in results if date.month==11]
#    dec = [str(date).split(' ')[0] for date in results if date.month==12]
#    calendar = {'January': jan, 'February': feb, 'March': march, 'April': april, 'May': may,
#    'June': june, 'July': july, 'August': aug, 'September': sept, 'October': octb,
#    'November': nov, 'December': dec}
    # Since calendar is a dictionary, the months will not be displayed in order.
    # As of now, I'm not sure what the best approach to fix this is.
    # Will come back to it later.
#    return {'calendar': calendar}



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

    # Our view function needs to return the packaged information we've requested in a format
    # that our jinja2 template can render. This format is a dictionary, whose keys are strings
    # that are referenced in the template.

    return {'today': convert_to_readable_format(today), 'events': dict(result)}

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
    return HTTPFound(request.route_url('home'))



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
    config.add_route('calendar', '/calendar')
    config.add_route('calendar_month', '/calendar_month')
    config.scan()
    app = config.make_wsgi_app()
    return app

if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)
