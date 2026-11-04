"""
Tests for the QR scan -> repair request -> technician queue flow.
"""

import pytest

from app.models import Machine, RepairRequest
from app.roles import EMPLOYEE_CREW, EMPLOYEE_TECHNICIAN
from app.services import (
    company_service,
    email_service,
    machine_service,
    repair_service,
    user_service
)


PASSWORD = "password123"


def make_company(name, tag):
    """Company with an admin, a crew member, a technician and a machine."""

    company, admin = company_service.create_company_with_admin(
        company_name=name,
        first_name="Admin",
        last_name=tag,
        email=f"admin-{tag}@test.com",
        password=PASSWORD
    )
    crew = user_service.create_employee(
        company_id=company.id,
        first_name="Crew",
        last_name=tag,
        email=f"crew-{tag}@test.com",
        password=PASSWORD,
        role=EMPLOYEE_CREW
    )
    tech = user_service.create_employee(
        company_id=company.id,
        first_name="Tech",
        last_name=tag,
        email=f"tech-{tag}@test.com",
        password=PASSWORD,
        role=EMPLOYEE_TECHNICIAN
    )
    machine = machine_service.create_machine(company.id, f"Mill {tag}")

    return {
        "company_id": company.id,
        "crew_id": crew.id,
        "machine_id": machine.id,
        "public_id": machine.public_id
    }


@pytest.fixture
def world(app):
    return {"a": make_company("Company A", "a"), "b": make_company("Company B", "b")}


def login(client, email):
    return client.post("/login", data={"login": email, "password": PASSWORD})


def report(client, public_id, severity="medium", description="Grinding noise"):
    return client.post(
        f"/repairs/report/{public_id}",
        data={"severity": severity, "description": description}
    )


# --- scanning -------------------------------------------------------------

def test_scan_when_signed_out_goes_to_login_with_next(client, world):
    public_id = world["a"]["public_id"]

    response = client.get(f"/m/{public_id}")

    assert response.status_code == 302
    assert response.headers["Location"] == f"/login?next=/m/{public_id}"


def test_login_returns_user_to_scanned_machine(client, world):
    public_id = world["a"]["public_id"]

    response = client.post(
        f"/login?next=/m/{public_id}",
        data={"login": "crew-a@test.com", "password": PASSWORD}
    )

    assert response.status_code == 302
    assert response.headers["Location"] == f"/m/{public_id}"


@pytest.mark.parametrize("target", [
    "https://evil.example/",
    "//evil.example/",
    "/\\evil.example",
    "javascript:alert(1)",
    "evil.example"
])
def test_login_ignores_unsafe_next(client, world, target):
    response = client.post(
        "/login",
        query_string={"next": target},
        data={"login": "crew-a@test.com", "password": PASSWORD}
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/dashboard"


def test_scan_shows_report_form(client, world):
    login(client, "crew-a@test.com")

    response = client.get(f"/m/{world['a']['public_id']}")

    assert response.status_code == 200
    assert b"Mill a" in response.data
    assert b'name="severity"' in response.data
    assert b'name="description"' in response.data


def test_scan_of_other_companys_machine_is_404(client, world):
    login(client, "crew-a@test.com")

    response = client.get(f"/m/{world['b']['public_id']}")

    assert response.status_code == 404


# --- submitting -----------------------------------------------------------

def test_crew_can_submit_request(client, app, world):
    login(client, "crew-a@test.com")

    response = report(client, world["a"]["public_id"], "medium", "Coolant leak")

    assert response.status_code == 302

    with app.app_context():
        saved = RepairRequest.query.one()
        assert saved.company_id == world["a"]["company_id"]
        assert saved.machine_id == world["a"]["machine_id"]
        assert saved.reported_by_id == world["a"]["crew_id"]
        assert saved.severity == "medium"
        assert saved.status == "submitted"
        assert saved.description == "Coolant leak"


def test_cannot_report_other_companys_machine(client, app, world):
    login(client, "crew-a@test.com")

    response = report(client, world["b"]["public_id"])

    assert response.status_code == 404

    with app.app_context():
        assert RepairRequest.query.count() == 0


def test_company_id_in_form_is_ignored(client, app, world):
    login(client, "crew-a@test.com")

    client.post(
        f"/repairs/report/{world['a']['public_id']}",
        data={
            "severity": "low",
            "description": "Sticky door",
            "company_id": world["b"]["company_id"]
        }
    )

    with app.app_context():
        assert RepairRequest.query.one().company_id == world["a"]["company_id"]


def test_signed_out_cannot_submit(client, app, world):
    response = report(client, world["a"]["public_id"])

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        assert RepairRequest.query.count() == 0


@pytest.mark.parametrize("severity,description", [
    ("", "Something broke"),
    ("critical", "Something broke"),
    ("high", ""),
    ("high", "   "),
    ("high", "x" * 2001)
])
def test_invalid_input_is_rejected(client, app, world, severity, description):
    login(client, "crew-a@test.com")

    response = report(client, world["a"]["public_id"], severity, description)

    assert response.status_code == 400

    with app.app_context():
        assert RepairRequest.query.count() == 0


def test_rejected_form_keeps_what_was_typed(client, world):
    login(client, "crew-a@test.com")

    response = report(client, world["a"]["public_id"], "", "Spindle stalls")

    assert b"Spindle stalls" in response.data


def test_service_refuses_machine_from_another_company(app, world):
    with app.app_context():
        from app.models import User

        reporter = User.query.get(world["a"]["crew_id"])
        other_machine = Machine.query.get(world["b"]["machine_id"])

        with pytest.raises(Exception) as error:
            repair_service.create_repair_request(
                reporter, other_machine, "low", "Not mine"
            )

        assert error.type.__name__ == "InvalidRepairRequestError"


def test_scan_page_mentions_existing_open_requests(client, world):
    login(client, "crew-a@test.com")
    report(client, world["a"]["public_id"])

    page = client.get(f"/m/{world['a']['public_id']}").get_data(as_text=True)

    # The template wraps this sentence over several lines.
    assert "1 open request already filed" in " ".join(page.split())


# --- notifications --------------------------------------------------------

def test_high_severity_emails_technicians_only(client, world):
    login(client, "crew-a@test.com")

    report(client, world["a"]["public_id"], "high", "Machine on fire")

    recipients = [m["To"] for m in email_service.sent_messages]
    assert recipients == ["tech-a@test.com"]
    assert "Mill a" in email_service.sent_messages[0]["Subject"]


def test_low_and_medium_do_not_send_email(client, world):
    login(client, "crew-a@test.com")

    report(client, world["a"]["public_id"], "low")
    report(client, world["a"]["public_id"], "medium")

    assert email_service.sent_messages == []


def test_email_failure_does_not_lose_the_request(client, app, world, monkeypatch):
    def broken_send(*args, **kwargs):
        raise OSError("mail server down")

    monkeypatch.setattr(email_service, "send_email", broken_send)
    login(client, "crew-a@test.com")

    response = report(client, world["a"]["public_id"], "high", "Smoke")

    assert response.status_code == 302

    with app.app_context():
        assert RepairRequest.query.count() == 1


# --- technician queue -----------------------------------------------------

def test_queue_orders_by_severity_then_age(client, world):
    login(client, "crew-a@test.com")
    report(client, world["a"]["public_id"], "low", "first-low")
    report(client, world["a"]["public_id"], "high", "the-high")
    report(client, world["a"]["public_id"], "medium", "the-medium")
    client.post("/logout")

    login(client, "tech-a@test.com")
    page = client.get("/repairs/").get_data(as_text=True)

    assert page.index("the-high") < page.index("the-medium") < page.index("first-low")


def test_queue_only_shows_own_company(client, world):
    login(client, "crew-b@test.com")
    report(client, world["b"]["public_id"], "high", "company-b-problem")
    client.post("/logout")

    login(client, "tech-a@test.com")
    page = client.get("/repairs/").get_data(as_text=True)

    assert "company-b-problem" not in page


def test_crew_cannot_view_queue(client, world):
    login(client, "crew-a@test.com")

    assert client.get("/repairs/").status_code == 403


def test_description_is_escaped_in_queue(client, world):
    login(client, "crew-a@test.com")
    report(client, world["a"]["public_id"], "low", "<script>alert(1)</script>")
    client.post("/logout")

    login(client, "tech-a@test.com")
    page = client.get("/repairs/").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in page


# --- changing status ------------------------------------------------------

def first_request_id(app):
    with app.app_context():
        return RepairRequest.query.order_by(RepairRequest.id).first().id


def set_status(client, request_id, status, view="open"):
    return client.post(
        f"/repairs/{request_id}/status",
        data={"status": status, "view": view}
    )


def file_request(client, world, who="crew-a@test.com", key="a"):
    login(client, who)
    report(client, world[key]["public_id"], "medium", "Belt is slipping")
    client.post("/logout")


@pytest.mark.parametrize("status", [
    "submitted", "acknowledged", "assigned", "in-progress",
    "waiting-for-parts", "completed", "rejected"
])
def test_technician_can_set_every_status(client, app, world, status):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    # Start from a different status so the change is a real change.
    set_status(client, request_id, "assigned" if status != "assigned" else "completed")
    response = set_status(client, request_id, status)

    assert response.status_code == 302

    with app.app_context():
        assert RepairRequest.query.get(request_id).status == status


def test_admin_can_change_status(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    set_status(client, request_id, "acknowledged")

    with app.app_context():
        assert RepairRequest.query.get(request_id).status == "acknowledged"


def test_status_change_records_who_and_when(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    set_status(client, request_id, "in-progress")

    with app.app_context():
        saved = RepairRequest.query.get(request_id)
        assert saved.status_updated_by.email == "tech-a@test.com"
        assert saved.status_updated_at is not None


def test_crew_cannot_change_status(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "crew-a@test.com")

    response = set_status(client, request_id, "completed")

    assert response.status_code == 403

    with app.app_context():
        assert RepairRequest.query.get(request_id).status == "submitted"


def test_signed_out_cannot_change_status(client, app, world):
    file_request(client, world)

    response = set_status(client, first_request_id(app), "completed")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        assert RepairRequest.query.one().status == "submitted"


def test_cannot_change_other_companys_request(client, app, world):
    file_request(client, world, who="crew-b@test.com", key="b")
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    response = set_status(client, request_id, "completed")

    assert response.status_code == 404

    with app.app_context():
        assert RepairRequest.query.get(request_id).status == "submitted"


@pytest.mark.parametrize("bad_status", ["", "action-needed", "down", "done", "COMPLETED"])
def test_invalid_status_is_rejected(client, app, world, bad_status):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    set_status(client, request_id, bad_status)

    with app.app_context():
        assert RepairRequest.query.get(request_id).status == "submitted"


def test_finished_requests_move_to_closed_tab(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    set_status(client, request_id, "completed")

    open_page = client.get("/repairs/").get_data(as_text=True)
    closed_page = client.get("/repairs/?view=closed").get_data(as_text=True)
    all_page = client.get("/repairs/?view=all").get_data(as_text=True)

    assert "Belt is slipping" not in open_page
    assert "Belt is slipping" in closed_page
    assert "Belt is slipping" in all_page


@pytest.mark.parametrize("status", ["completed", "rejected"])
def test_closed_requests_do_not_count_as_open_on_scan_page(client, app, world, status):
    file_request(client, world)
    login(client, "tech-a@test.com")
    set_status(client, first_request_id(app), status)
    client.post("/logout")

    login(client, "crew-a@test.com")
    page = client.get(f"/m/{world['a']['public_id']}").get_data(as_text=True)

    assert "already filed" not in page


def test_waiting_for_parts_still_counts_as_open(client, app, world):
    file_request(client, world)
    login(client, "tech-a@test.com")
    set_status(client, first_request_id(app), "waiting-for-parts")

    page = client.get("/repairs/").get_data(as_text=True)

    assert "Belt is slipping" in page
    assert "Waiting for Parts" in page


# --- assigning ------------------------------------------------------------

def user_id(app, email):
    from app.models import User

    with app.app_context():
        return User.query.filter_by(email=email).one().id


def assign(client, request_id, assignee_id, view="open"):
    return client.post(
        f"/repairs/{request_id}/assign",
        data={"assignee_id": assignee_id, "view": view}
    )


def saved_request(app, request_id):
    with app.app_context():
        saved = RepairRequest.query.get(request_id)
        return saved.assigned_to_id, saved.status


def add_second_technician(app, world):
    with app.app_context():
        tech2 = user_service.create_employee(
            company_id=world["a"]["company_id"],
            first_name="Tech2",
            last_name="a",
            email="tech2-a@test.com",
            password=PASSWORD,
            role=EMPLOYEE_TECHNICIAN
        )
        return tech2.id


def test_technician_can_assign_themselves(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    tech_id = user_id(app, "tech-a@test.com")
    login(client, "tech-a@test.com")

    response = assign(client, request_id, tech_id)

    assert response.status_code == 302
    assert saved_request(app, request_id) == (tech_id, "assigned")


def test_self_assignment_does_not_email_anyone(client, app, world):
    file_request(client, world)
    login(client, "tech-a@test.com")

    assign(client, first_request_id(app), user_id(app, "tech-a@test.com"))

    assert email_service.sent_messages == []


def test_technician_cannot_assign_someone_else(client, app, world):
    tech2_id = add_second_technician(app, world)
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")

    response = assign(client, request_id, tech2_id)

    assert response.status_code == 403
    assert saved_request(app, request_id) == (None, "submitted")


def test_technician_cannot_take_request_held_by_another(client, app, world):
    tech2_id = add_second_technician(app, world)
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")
    assign(client, request_id, tech2_id)
    client.post("/logout")

    login(client, "tech-a@test.com")
    response = assign(client, request_id, user_id(app, "tech-a@test.com"))

    assert response.status_code == 403
    assert saved_request(app, request_id)[0] == tech2_id


def test_technician_cannot_unassign_someone_else(client, app, world):
    tech2_id = add_second_technician(app, world)
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")
    assign(client, request_id, tech2_id)
    client.post("/logout")

    login(client, "tech-a@test.com")
    response = assign(client, request_id, "")

    assert response.status_code == 403
    assert saved_request(app, request_id)[0] == tech2_id


def test_technician_can_unassign_themselves(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    tech_id = user_id(app, "tech-a@test.com")
    login(client, "tech-a@test.com")
    assign(client, request_id, tech_id)

    assign(client, request_id, "")

    # With nobody holding it, it can't still read "Assigned".
    assert saved_request(app, request_id) == (None, "acknowledged")


def test_admin_can_assign_a_technician_and_they_are_emailed(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    tech_id = user_id(app, "tech-a@test.com")
    login(client, "admin-a@test.com")

    assign(client, request_id, tech_id)

    assert saved_request(app, request_id) == (tech_id, "assigned")
    assert [m["To"] for m in email_service.sent_messages] == ["tech-a@test.com"]


def test_admin_can_reassign_and_unassign(client, app, world):
    tech2_id = add_second_technician(app, world)
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    assign(client, request_id, user_id(app, "tech-a@test.com"))
    assign(client, request_id, tech2_id)
    assert saved_request(app, request_id)[0] == tech2_id

    assign(client, request_id, "")
    assert saved_request(app, request_id) == (None, "acknowledged")


def test_admin_can_assign_themselves(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    admin_id = user_id(app, "admin-a@test.com")
    login(client, "admin-a@test.com")

    assign(client, request_id, admin_id)

    assert saved_request(app, request_id)[0] == admin_id


def test_admin_cannot_assign_a_crew_member(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    assign(client, request_id, user_id(app, "crew-a@test.com"))

    assert saved_request(app, request_id)[0] is None


def test_cannot_assign_a_user_from_another_company(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    assign(client, request_id, user_id(app, "tech-b@test.com"))

    assert saved_request(app, request_id)[0] is None


def test_cannot_assign_another_companys_request(client, app, world):
    file_request(client, world, who="crew-b@test.com", key="b")
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    response = assign(client, request_id, user_id(app, "admin-a@test.com"))

    assert response.status_code == 404
    assert saved_request(app, request_id)[0] is None


@pytest.mark.parametrize("bad_value", ["abc", "99999", "-1", "1.5"])
def test_junk_assignee_is_rejected_without_error(client, app, world, bad_value):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "admin-a@test.com")

    response = assign(client, request_id, bad_value)

    assert response.status_code == 302
    assert saved_request(app, request_id)[0] is None


def test_crew_and_signed_out_cannot_assign(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    crew_id = user_id(app, "crew-a@test.com")

    signed_out = assign(client, request_id, crew_id)
    assert signed_out.status_code == 302
    assert "/login" in signed_out.headers["Location"]

    login(client, "crew-a@test.com")
    assert assign(client, request_id, crew_id).status_code == 403
    assert saved_request(app, request_id)[0] is None


def test_assigning_does_not_reopen_a_closed_request(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    login(client, "tech-a@test.com")
    set_status(client, request_id, "completed")

    assign(client, request_id, user_id(app, "tech-a@test.com"))

    assert saved_request(app, request_id)[1] == "completed"


def test_assigned_to_me_tab_lists_only_my_requests(client, app, world):
    tech2_id = add_second_technician(app, world)
    login(client, "crew-a@test.com")
    report(client, world["a"]["public_id"], "low", "mine-problem")
    report(client, world["a"]["public_id"], "low", "theirs-problem")
    client.post("/logout")

    login(client, "tech-a@test.com")
    with app.app_context():
        ids = [r.id for r in RepairRequest.query.order_by(RepairRequest.id)]
    assign(client, ids[0], user_id(app, "tech-a@test.com"))
    client.post("/logout")
    login(client, "admin-a@test.com")
    assign(client, ids[1], tech2_id)
    client.post("/logout")

    login(client, "tech-a@test.com")
    page = client.get("/repairs/?view=mine").get_data(as_text=True)

    assert "mine-problem" in page
    assert "theirs-problem" not in page


def test_queue_shows_who_it_is_assigned_to(client, app, world):
    file_request(client, world)
    login(client, "admin-a@test.com")
    assign(client, first_request_id(app), user_id(app, "tech-a@test.com"))

    page = client.get("/repairs/").get_data(as_text=True)

    assert "Tech a" in " ".join(page.split())


def test_deleting_a_technician_unassigns_their_requests(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)
    tech_id = user_id(app, "tech-a@test.com")
    login(client, "tech-a@test.com")
    assign(client, request_id, tech_id)
    client.post("/logout")

    with app.app_context():
        from app.models import User
        user_service.delete_employee(User.query.get(tech_id))

    assert saved_request(app, request_id) == (None, "acknowledged")


def test_deleting_the_reporter_keeps_the_request(client, app, world):
    file_request(client, world)
    request_id = first_request_id(app)

    with app.app_context():
        from app.models import User
        user_service.delete_employee(User.query.get(world["a"]["crew_id"]))
        saved = RepairRequest.query.get(request_id)
        assert saved is not None
        assert saved.reported_by_id is None
