"""
Security tests for RepRequest.

Covers CSRF protection, cookie settings, response headers and
the minimum password length on registration.
"""

import pytest

from app import create_app
from app.extensions import db
from app.models import User
from config import TestingConfig


class CsrfTestingConfig(TestingConfig):
    """
    Same as TestingConfig, but with CSRF protection turned on.
    """

    WTF_CSRF_ENABLED = True


@pytest.fixture
def csrf_client():
    """
    A test client for an app that enforces CSRF tokens.
    """

    csrf_app = create_app(CsrfTestingConfig)

    with csrf_app.app_context():
        db.create_all()

        yield csrf_app.test_client()

        db.session.remove()
        db.drop_all()


def test_post_without_csrf_token_is_rejected(csrf_client):
    """
    A form post without a CSRF token should be refused.
    """

    response = csrf_client.post(
        "/login",
        data={
            "login": "admin@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 400


def test_forms_include_csrf_token(csrf_client):
    """
    Pages with forms should include the hidden CSRF field.
    """

    for path in ("/login", "/register", "/forgot-password"):
        response = csrf_client.get(path)

        assert b'name="csrf_token"' in response.data


def test_cookie_settings():
    """
    Session and remember-me cookies should use the setting
    names Flask actually reads.
    """

    config = TestingConfig

    assert config.SESSION_COOKIE_SAMESITE == "Lax"
    assert config.REMEMBER_COOKIE_SAMESITE == "Lax"
    assert config.SESSION_COOKIE_HTTPONLY is True
    assert config.REMEMBER_COOKIE_SECURE == config.SESSION_COOKIE_SECURE


def test_security_headers(client):
    """
    Every page should send the security response headers.
    """

    response = client.get("/login")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert response.headers["Cache-Control"] == "no-store"


def test_production_refuses_dev_secret_key(monkeypatch):
    """
    With APP_ENV=production, the app should not start using the
    development SECRET_KEY.
    """

    class DevKeyConfig(TestingConfig):
        SECRET_KEY = "dev-secret-key-change-before-production"

    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(RuntimeError):
        create_app(DevKeyConfig)


def test_registration_requires_long_password(client, app):
    """
    Registration should refuse passwords under 8 characters.
    """

    response = client.post(
        "/register",
        data={
            "company_name": "Test Company",
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@test.com",
            "password": "short"
        }
    )

    assert response.status_code == 200
    assert b"at least 8 characters" in response.data

    with app.app_context():
        assert User.query.filter_by(email="admin@test.com").first() is None
