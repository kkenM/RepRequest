"""
User-session tests for RepRequest.
"""

from app.models import User
from app.roles import EMPLOYEE_CREW
from app.services import company_service, user_service


def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password}
    )


def create_admin_and_crew(app):
    with app.app_context():
        company, admin = company_service.create_company_with_admin(
            company_name="Test Company",
            first_name="Admin",
            last_name="User",
            email="admin@test.com",
            password="password123"
        )
        user_service.create_employee(
            company_id=company.id,
            first_name="Crew",
            last_name="User",
            email="crew@test.com",
            password="password123",
            role=EMPLOYEE_CREW
        )
        return company.id


def is_signed_in(client):
    return client.get("/dashboard").status_code == 200


def test_cookie_stores_token_not_user_id(client, app):
    create_admin_and_crew(app)
    login(client, "crew@test.com", "password123")

    user = User.query.filter_by(email="crew@test.com").first()

    with client.session_transaction() as session:
        assert session["_user_id"] == user.session_token
        assert session.permanent


def test_logout_ends_session(client, app):
    create_admin_and_crew(app)
    login(client, "crew@test.com", "password123")

    client.post("/logout")

    assert not is_signed_in(client)


def test_logout_all_ends_sessions_on_other_devices(app):
    create_admin_and_crew(app)
    phone, laptop = app.test_client(), app.test_client()

    login(phone, "crew@test.com", "password123")
    login(laptop, "crew@test.com", "password123")

    laptop.post("/logout/all")

    assert not is_signed_in(phone)
    assert not is_signed_in(laptop)


def test_deleted_employee_cookie_cannot_reach_reused_id(app):
    company_id = create_admin_and_crew(app)
    crew_client = app.test_client()
    login(crew_client, "crew@test.com", "password123")

    old_crew = User.query.filter_by(email="crew@test.com").first()
    user_service.delete_employee(old_crew)

    # SQLite usually gives this account the deleted ID.
    user_service.create_employee(
        company_id=company_id,
        first_name="New",
        last_name="Hire",
        email="new@test.com",
        password="password123",
        role=EMPLOYEE_CREW
    )

    assert not is_signed_in(crew_client)


def test_pages_are_not_cached_by_browser(client, app):
    create_admin_and_crew(app)

    login_page = client.get("/login")
    assert login_page.headers["Cache-Control"] == "no-store"

    login(client, "crew@test.com", "password123")

    dashboard = client.get("/dashboard")
    assert dashboard.headers["Cache-Control"] == "no-store"