# RepRequest Architecture

## Overview

RepRequest is a Flask-based multi-company maintenance and repair-request platform.

A company creates an account and receives its own organization within the system.

Users belong to a company and have different roles such as:

```text
Company Administrator
Crew Employee
Technician
```

Future RepRequest functionality will include company-owned machines, QR codes, repair requests, technician workflows, and repair-status tracking.

The architecture is designed so that new features can be added without placing all application behavior into one large Flask file.

---

# Application Structure

```text
RepRequest/
│
├── run.py
├── config.py
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── authorization.py
│   ├── roles.py
│   ├── errors.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   └── user.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── company_service.py
│   │   └── user_service.py
│   │
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── admin/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── templates/
│   └── static/
│
├── docs/
│
└── instance/
```

---

# Application Startup

The application starts through:

```text
run.py
```

`run.py` calls:

```python
create_app()
```

from:

```text
app/__init__.py
```

The application factory is responsible for assembling the Flask application.

The startup flow is:

```text
run.py
    ↓
create_app()
    ↓
Load configuration
    ↓
Initialize extensions
    ↓
Register Blueprints
    ↓
Register error handlers
    ↓
Initialize database support
    ↓
Return Flask application
```

Feature-specific behavior should not be added directly to the application factory.

---

# Flask Extensions

Shared Flask extension objects live in:

```text
app/extensions.py
```

Examples include:

```text
SQLAlchemy
Flask-Login
```

Extensions are created independently and attached to the Flask application through the application factory.

This avoids tying extensions to one global Flask instance and makes testing easier.

---

# Blueprints

RepRequest organizes HTTP routes into Flask Blueprints.

Current Blueprints:

```text
main
auth
admin
```

## Main Blueprint

Location:

```text
app/main/
```

Responsible for general application pages.

Examples:

```text
Home
Dashboard
```

## Authentication Blueprint

Location:

```text
app/auth/
```

Responsible for identity and sessions.

Examples:

```text
Company registration
Login
Logout
Flask-Login user loading
```

Authentication answers:

```text
Who is the current user?
```

## Administration Blueprint

Location:

```text
app/admin/
```

Responsible for company-administrator HTTP operations.

Examples:

```text
View employees
Create employees
Edit employees
Delete employees
```

Authorization determines whether a user may access these operations.

---

# Models

Database entities live in:

```text
app/models/
```

Models describe persisted data and relationships.

Current models:

```text
Company
User
```

Future models may include:

```text
Machine
RepairRequest
RepairComment
```

Models should contain behavior intrinsic to the entity.

For example:

```python
user.set_password(...)
```

belongs to `User` because password handling is part of the User entity.

Large workflows involving multiple entities should generally use services.

---

# Services

Application operations live in:

```text
app/services/
```

Services sit between routes and models.

Example flow:

```text
HTTP request
    ↓
Admin route
    ↓
user_service.create_employee()
    ↓
User model
    ↓
Database
```

Services allow business logic to be reused independently of Flask routes.

They also make automated testing easier because business behavior can be tested without simulating a browser request.

---

# Authorization

Reusable authorization behavior lives in:

```text
app/authorization.py
```

Example:

```python
@company_admin_required
def create_employee():
    ...
```

Authorization answers:

```text
What is this authenticated user allowed to do?
```

Authentication and authorization are intentionally separate concerns.

---

# Roles

Role definitions live in:

```text
app/roles.py
```

Internal role values should not be repeatedly hard-coded throughout the application.

The role module provides:

```text
role constants
employee role groups
human-readable labels
employee role options
```

This creates one source of truth for RepRequest roles.

---

# Error Handling

Application-wide HTTP error handlers live in:

```text
app/errors.py
```

For example:

```text
403 Forbidden
```

should not be implemented separately in every feature module.

---

# Templates

Templates are organized by feature:

```text
app/templates/
├── main/
├── auth/
├── admin/
└── errors/
```

Future features should follow the same pattern:

```text
machines/
repairs/
```

Templates control presentation only.

They must not be relied upon for security.

For example:

```html
{% if current_user.is_company_admin %}
```

may hide an administrative link, but the route must still contain server-side authorization.

---

# Multi-Company Data Isolation

RepRequest stores multiple companies in one database.

Each user belongs to one company through:

```text
company_id
```

Company-owned records must be accessed within the authenticated user's company.

Example:

```python
employee = user_service.get_company_employee(
    company_id=current_user.company_id,
    employee_id=employee_id
)
```

The system must never trust an arbitrary browser-supplied `company_id` when determining ownership.

This protects against a user manually changing URLs or requests to access another company's data.

---

# Design Boundaries

The project follows these boundaries:

```text
Routes know about HTTP.
Services know about business operations.
Models know about stored entities.
Authorization knows about access control.
Roles know about role definitions.
Templates know about presentation.
```

A layer should avoid taking over responsibilities belonging to another layer.

For example, a service should not do:

```python
render_template(...)
```

because HTML rendering belongs to the route/presentation layer.

A route should avoid doing:

```python
db.session.add(...)
db.session.commit()
```

when that operation is part of reusable business logic.

---

# Future Feature Structure

A new feature should generally receive its own Blueprint when it becomes a distinct part of the application.

For example:

```text
app/
├── machines/
│   ├── __init__.py
│   └── routes.py
│
└── repairs/
    ├── __init__.py
    └── routes.py
```

Associated business logic would live in:

```text
services/machine_service.py
services/repair_service.py
```

Associated database entities would live in:

```text
models/machine.py
models/repair_request.py
```

Associated templates would live in:

```text
templates/machines/
templates/repairs/
```

This allows features to grow independently while following a common architecture.

---

# Primary Design Goals

RepRequest prioritizes:

```text
Manageable complexity
Clear module responsibilities
Company data isolation
Reusable business logic
Secure authorization
Ease of team development
Low merge-conflict risk
Testability
Future extensibility
```

New design decisions should support these goals whenever practical.