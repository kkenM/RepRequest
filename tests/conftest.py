"""
Shared pytest fixtures for RepRequest.

Tests run against an isolated in-memory database and must never
modify the developer's normal instance/accounts.db database.
"""

import pytest
from flask import g

from app import create_app
from app.extensions import db
from config import TestingConfig


@pytest.fixture
def app():
    """
    Create a fresh RepRequest application and database
    for each test.
    """

    test_app = create_app(
        TestingConfig
    )

    """
    The fixture keeps one app context open for the whole test, so
    Flask's `g` would otherwise be shared by every request. Clear
    Flask-Login's cached user after each request so the next one
    reloads the user from its own session cookie, as in production  
    """
    @test_app.teardown_request
    def forget_cached_user(error):
        g.pop("_login_user", None)

    with test_app.app_context():

        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Provide Flask's test HTTP client.
    """

    return app.test_client()