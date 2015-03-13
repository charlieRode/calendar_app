from contextlib import closing
from pyramid import testing
import pytest
import datetime
from app import connect_db, TABLE1_SCHEMA, TABLE2_SCHEMA

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
        """Thank you to Gringo Suave @StackOverflow!"""
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
