from contextlib import closing
from pyramid import testing
import pytest

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
