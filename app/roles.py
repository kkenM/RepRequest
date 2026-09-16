"""
Role definitions for RepRequest.

All application role values are defined here so routes,
services, models, and future features use the same values.

Do not hard-code role strings elsewhere in Python code.
"""


# Company-level administrator
COMPANY_ADMIN = "company-admin"


# Standard employee roles
EMPLOYEE_CREW = "employee-crew"
EMPLOYEE_TECHNICIAN = "employee-technician"


# Roles that may be assigned to employee accounts.
EMPLOYEE_ROLES = (
    EMPLOYEE_CREW,
    EMPLOYEE_TECHNICIAN
)


# Every role currently supported by RepRequest.
ALL_ROLES = (
    COMPANY_ADMIN,
    EMPLOYEE_CREW,
    EMPLOYEE_TECHNICIAN
)


# Human-readable role names for the user interface.
ROLE_LABELS = {
    COMPANY_ADMIN: "Company Administrator",
    EMPLOYEE_CREW: "Crew Employee",
    EMPLOYEE_TECHNICIAN: "Technician"
}

# Roles that administrators may choose when creating
# or editing employee accounts.
EMPLOYEE_ROLE_OPTIONS = (
    (
        EMPLOYEE_CREW,
        ROLE_LABELS[EMPLOYEE_CREW]
    ),
    (
        EMPLOYEE_TECHNICIAN,
        ROLE_LABELS[EMPLOYEE_TECHNICIAN]
    )
)