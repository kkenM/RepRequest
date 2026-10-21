from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user

from app.authorization import company_admin_required, role_required
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN
from app.services import machine_service
from app.services.qr_service import machine_qr_png, machine_scan_url


machines_bp = Blueprint(
    "machines",
    __name__,
    url_prefix="/machines"
)


# read the name of the machine from the submitted form
def read_machine_name():

    return request.form.get("name", "").strip()


# Return the companies machine
def get_machine_or_404(machine_id):

    machine = machine_service.get_company_machine(
        current_user.company_id,
        machine_id
    )

    if machine is None:
        abort(404)

    return machine


# Show all machines for the sign-ed in user's company
@machines_bp.route("/", strict_slashes=False)
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def index():

    machines = machine_service.get_company_machines(
        current_user.company_id
    )

    return render_template(
        "machines/index.html",
        machines=machines,
        is_admin=current_user.role == COMPANY_ADMIN
    )


# Show the form for creation, and registering a new machine
@machines_bp.route("/create", methods=["GET", "POST"])
@company_admin_required
def create():

    name = ""

    if request.method == "POST":
        name = read_machine_name()

        if not name:
            flash("Machine name is required.", "danger")
        else:
            machine = machine_service.create_machine(
                current_user.company_id,
                name
            )

            flash("Machine created.", "success")

            return redirect(
                url_for("machines.detail", machine_id=machine.id)
            )

    return render_template(
        "machines/form.html",
        machine=None,
        name=name
    )


# Display a machine's details
@machines_bp.route("/<int:machine_id>")
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def detail(machine_id):

    machine = get_machine_or_404(machine_id)

    return render_template(
        "machines/detail.html",
        machine=machine,
        is_admin=current_user.role == COMPANY_ADMIN
    )


# Show the rename form and update the machine
@machines_bp.route("/<int:machine_id>/edit", methods=["GET", "POST"])
@company_admin_required
def edit(machine_id):

    machine = get_machine_or_404(machine_id)

    name = machine.name

    if request.method == "POST":
        name = read_machine_name()

        if not name:
            flash("Machine name is required.", "danger")
        else:
            machine_service.update_machine(machine, name)

            flash("Machine updated.", "success")

            return redirect(
                url_for("machines.detail", machine_id=machine.id)
            )

    return render_template(
        "machines/form.html",
        machine=machine,
        name=name
    )


# Delete a machine, then return back to machine creation
@machines_bp.route("/<int:machine_id>/delete", methods=["POST"])
@company_admin_required
def delete(machine_id):

    machine = get_machine_or_404(machine_id)

    machine_service.delete_machine(machine)

    flash("Machine deleted.", "success")

    return redirect(url_for("machines.index"))


# Return the machine's QR code as a PNG
@machines_bp.route("/<int:machine_id>/qr.png")
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def qr_image(machine_id):

    machine = get_machine_or_404(machine_id)

    response = Response(
        machine_qr_png(machine),
        mimetype="image/png"
    )

    if request.args.get("download") == "1":
        if current_user.role != COMPANY_ADMIN:
            abort(403)

        response.headers["Content-Disposition"] = (
            f'attachment; filename="machine-{machine.id}-qr.png"'
        )

    return response


# Display a printable QR label for a machine
@machines_bp.route("/<int:machine_id>/label")
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def label(machine_id):

    machine = get_machine_or_404(machine_id)

    return render_template(
        "machines/label.html",
        machine=machine,
        scan_url=machine_scan_url(machine)
    )