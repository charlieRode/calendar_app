from contextlib import closing
from pyramid import testing
import pytest
import datetime
import os
from app import connect_db, TABLE1_SCHEMA, TABLE2_SCHEMA, ADD_EVENT

TEST_DSN = 'dbname=test_calendar_db user=store'


# NOTE: We are writing new init_db function instead of importing the one we've
# already written.
# Why?
# Because our init_db function in app.py relies on the settings of the
# environment, which won't be the same as our testing environment.
# This init_db takes settings as an argument, so that we can explicitly choose
# what settings to test.
def init_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute(TABLE1_SCHEMA)
        db.cursor().execute(TABLE2_SCHEMA)
        db.commit()

    def populate_calendar(settings):
        INSERT_DAY = """
        INSERT INTO days (date, dow) VALUES (%s, %s)
        """
        date = datetime.datetime.today()
        dow = (date.weekday() + 1) % 7  # <- Sunday: 0, Monday : 1, ..., Saturday: 6
        with closing(connect_db(settings)) as db:
            for i in xrange(365):
                db.cursor().execute(INSERT_DAY, [str(date).split(" ")[0], dow])
                date += datetime.timedelta(1)
                dow = (date.weekday() + 1) % 7
            db.commit()

    populate_calendar(settings)


def clear_db(settings):
    with closing(connect_db(settings)) as db:
        # Must drop events table first, as it has a foreign
        # field that references the days table.
        db.cursor().execute("DROP TABLE events")
        db.cursor().execute("DROP TABLE days")
        db.commit()


def clear_events(settings):
    with closing(connect_db(settings)) as db:
        # In PSQL, if the WHERE clause is missing from a DELETE
        # statement, then the deletion applies to all rows.
        db.cursor().execute("DELETE FROM events")


def run_query(db, query, params=(), get_results=True):
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    results = None
    if get_results:
        results = cursor.fetchall()
    return results


@pytest.fixture(scope='function')
def app(db):
    from app import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    return TestApp(app)


@pytest.fixture(scope='session')
def db(request):
    """set up and tear down a database"""
    settings = {'db': TEST_DSN}
    init_db(settings)

    def cleanup():
        clear_db(settings)

    request.addfinalizer(cleanup)

    return settings


@pytest.yield_fixture(scope='function')
def mock_request(db, request):  # <- registered fixtures as arguments
    """mock a request with a database attached"""
    # By assigning db to 'settings' we are running the db fixture,
    # and return the value of settings there.
    settings = db
    req = testing.DummyRequest()
    with closing(connect_db(settings)) as db:
        req.db = db  # <- Hang our test_db on our dummy request
        req.exception = None
        yield req

        # after a test has run, we clear out events for isolation
        clear_events(settings)

# NOTE:
# Because "yield" preserves internal state, the entire test happns *inside the
# context manager scope* !!
# Use yield fixutes when you want to maintain the program state created by your
# fixture

def test_read_day_empty(mock_request):
    from app import read_day
    today = str(datetime.datetime.today()).split(' ')[0]
    # Because our read_day function will depend upon a given date
    # we need to hang a date on our mock_request.
    mock_request.params['date'] = today
    result = read_day(mock_request)
    assert type(result) == dict
    assert len(result['events']) == 0


def test_add_event(mock_request):
    from app import add_event
    fields = ('description', 'date', 'time')
    desc = "Dinner"
    time = '17:00'
    date = str(datetime.datetime.today()).split(' ')[0]
    expected = (desc, date, time)
    mock_request.params = dict(zip(fields, expected))
    # Assert that we have no entries at start
    rows = run_query(mock_request.db, "SELECT * FROM events")
    assert len(rows) == 0
    result = add_event(mock_request)
    mock_request.db.commit()

    rows = run_query(mock_request.db, "SELECT description, date, time FROM events")
    assert len(rows) == 1
    actual = rows[0]
    # For testing purposes, convert objects into strings
    actual = tuple([str(actual[x]) for x in xrange(3)])
    # Expect '17:00:00' instead of '17:00'
    expected = (expected[0], expected[1], '17:00:00')
    for idx, val in enumerate(expected):
        assert val == actual[idx]


def test_read_day(mock_request):
    from app import read_day
    today = str(datetime.datetime.today()).split(' ')[0]
    # As above, we need to supply our test request-object with
    # information about a date, so that read_day can query the DB.
    mock_request.params['date'] = today
    event1 = ('Church', today, '8:00')
    event2 = ('Dinner', today, '17:00')
    run_query(mock_request.db, ADD_EVENT, event1, False)
    run_query(mock_request.db, ADD_EVENT, event2, False)
    result = read_day(mock_request)
    assert len(result['events']) == 2
    assert result['events']['8:00 AM'] == 'Church'
    assert result['events']['5:00 PM'] == 'Dinner'


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No events today!'
    assert expected in actual


@pytest.fixture(scope='function')
def entry(db, request):
    """provide a single event entry to the database"""
    INSERT_EVENT = """
    INSERT INTO events (description, date, time) VALUES (%s, %s, %s)
    """
    settings = db
    expected = ('Dinner', '2015-03-20', '17:00:00')
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_EVENT, expected, False)
        db.commit()

    def cleanup():
        clear_events(settings)

    request.addfinalizer(cleanup)

    return expected


def test_listing(app, entry):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = ('Dinner', '5:00 PM')
    for item in expected:
        assert item in actual
