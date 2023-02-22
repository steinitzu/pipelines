from typing import Iterator

import pytest

from tests.sql_database.sql_source import SQLAlchemySourceDB


@pytest.fixture(scope='session')
def sql_source_db() -> Iterator[SQLAlchemySourceDB]:
    db = SQLAlchemySourceDB()
    try:
        db.create_schema()
        db.create_tables()
        db.insert_data()
        yield db
    finally:
        db.drop_schema()

