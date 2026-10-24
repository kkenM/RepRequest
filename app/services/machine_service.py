
from app.extensions import db
from app.models import Machine

# Returns the machines that belong to the company
def get_company_machines(company_id):

    return Machine.query.filter_by(
        company_id=company_id
    ).order_by(
        Machine.name
    ).all()

# Retrieve one machine that belongs to the specific company accessing it
def get_company_machine(company_id, machine_id):

    return Machine.query.filter(
        Machine.id == machine_id,
        Machine.company_id == company_id
    ).first()

# Retrieves the machine by the ID printed in its QR Code
def get_machine_by_public_id(public_id):

    return Machine.query.filter_by(
        public_id=public_id
    ).first()

# Creates a machine for the specific company
def create_machine(company_id, name):

    machine = Machine(
        company_id=company_id,
        name=name.strip()
    )

    db.session.add(machine)
    db.session.commit()

    return machine


# Updates the machine, only used for renaming the machine
# Machines keeps the same QR label and ID
def update_machine(machine, name):

    machine.name = name.strip()

    db.session.commit()

    return machine

# Permanately deletes a machine
def delete_machine(machine):

    db.session.delete(machine)
    db.session.commit()