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

The machine, repair-request and maintenance-log features are not implemented yet, but each already has its own Blueprint serving a placeholder page. This keeps the navigation, the URL structure and the authorization rules in place and testable before the feature behind them is built.

The architecture is designed so that new features can be added without placing all application behavior into one large Flask file.

The front end is server-rendered Jinja2. All pages inherit one base layout and share one stylesheet, so presentation is defined in a single place rather than repeated in every template.

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
│   ├── machines/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── repairs/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── logs/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── partials/
│   │   ├── main/
│   │   ├── auth/
│   │   ├── admin/
│   │   ├── machines/
│   │   ├── repairs/
│   │   ├── logs/
│   │   └── errors/
│   │
│   └── static/
│       └── css/
│           └── style.css
│
├── tests/
│
├── migrations/
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
Register template context processors
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
machines     (placeholder)
repairs      (placeholder)
logs         (placeholder)
```

A placeholder Blueprint is a real Blueprint with real authorization. Only the page body is a "coming soon" panel. It should be filled in rather than replaced when the feature is built.

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

## Machines Blueprint

Location:

```text
app/machines/
```

URL prefix:

```text
/machines
```

Responsible for the machine registry: registering machines, printing QR labels, and resolving a scanned QR token to one machine of one company.

Restricted to:

```text
Company Administrator
Technician
```

Not implemented yet. Business logic will live in:

```text
app/services/machine_service.py
```

## Repairs Blueprint

Location:

```text
app/repairs/
```

URL prefix:

```text
/repairs
```

Responsible for repair-request submission and the technician repair queue, including the status transitions a request may make.

Restricted to:

```text
Company Administrator
Technician
```

Crew employees will be able to submit a request once machines exist, so this Blueprint's authorization will widen when the feature is built.

Not implemented yet. Business logic will live in:

```text
app/services/repair_service.py
```

## Logs Blueprint

Location:

```text
app/logs/
```

URL prefix:

```text
/maintenance-logs
```

Responsible for maintenance logs and per-machine service history.

Restricted to:

```text
Company Administrator
Technician
```

Not implemented yet. Business logic will live in:

```text
app/services/log_service.py
```

---

# Template Context Processors

Values that every template needs are injected by the application factory rather than passed by every route.

For example, the footer copyright year:

```python
@app.context_processor
def inject_template_globals():
    return {
        "now_year": datetime.utcnow().year
    }
```

A Blueprint may register its own context processor when a value is only needed by that feature's templates.

For example, valid employee role choices are injected by the admin Blueprint:

```python
@admin_bp.context_processor
def inject_employee_role_options():
    ...
```

Context processors should supply presentation values only. They must not perform authorization or expose another company's data.

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
├── base.html
├── partials/
├── main/
├── auth/
├── admin/
├── machines/
├── repairs/
├── logs/
└── errors/
```

Future features should follow the same pattern: one folder per Blueprint.

## Base Layout

Every authenticated page extends:

```text
app/templates/base.html
```

The base layout owns the page shell:

```text
document head and stylesheet link
navigation bar
flash messages
page container
footer
```

A feature template therefore contains only its own content:

```html
{% extends "base.html" %}
{% block title %}Requests - RepRequest{% endblock %}

{% block content %}
    ...
{% endblock %}
```

Available blocks:

```text
title        browser tab title
page_class   extra class on the page container
head_extra   additional head elements
content      the page body
```

## Partials

Shared fragments live in:

```text
app/templates/partials/
```

Current partials:

```text
_topbar.html        navigation bar
_flashes.html       flash messages
_footer.html        page footer
_coming_soon.html   placeholder body for unbuilt features
```

A partial is included rather than extended:

```html
{% include "partials/_topbar.html" %}
```

The navigation bar exists once, in `_topbar.html`. Navigation links should not be written directly into feature templates, so that adding a tab is a one-file change.

The public home page and the login and register pages do not extend `base.html`, because they must render for anonymous visitors and do not use the application navigation. They include the same partials instead.

## Templates and Security

Templates control presentation only.

They must not be relied upon for security.

For example:

```html
{% if current_user.is_company_admin %}
```

may hide an administrative link, but the route must still contain server-side authorization.

The navigation bar hides tabs the current user's role cannot use. Every route behind those tabs still carries its own decorator:

```python
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
```

so typing the URL directly returns 403 rather than the page.

---

# Presentation and Styling

All styling lives in one stylesheet:

```text
app/static/css/style.css
```

It is linked once, by the base layout:

```html
<link rel="stylesheet"
      href="{{ url_for('static', filename='css/style.css') }}">
```

Templates should not use inline `style` attributes or `<style>` blocks for anything reusable.

## Design Tokens

Colour, spacing, radius, shadow and font values are defined once as CSS custom properties:

```css
:root {
    --primary: var(--indigo-600);
    --ink: var(--slate-900);
    --surface: #FFFFFF;
    --canvas: var(--slate-50);
    --sp-4: 1rem;
    --r-md: 10px;
}
```

New rules should use these tokens rather than literal values, so the whole application can be restyled from the token block.

## Stylesheet Organization

The stylesheet is grouped into numbered sections:

```text
 1. Design tokens
 2. Reset and base
 3. Layout
 4. Navigation
 5. Buttons
 6. Cards and panels
 7. Tables
 8. Forms
 9. Badges and status
10. Marketing home page
11. Utilities and responsive
```

New styles belong in the matching section.

## Class Naming

Classes describe a component and its parts:

```text
.card            component
.card__head      part of the component
.btn--primary    variant of the component
```

Avoid classes named after a specific page, because a component used on two pages should not need two rules.

## Reusable Components

Before adding new CSS, check whether an existing component fits:

```text
.card            bordered panel with optional head and body
.table           employee-style data table
.form__control   text input, select
.btn             button and link-button, with variants
.badge           role, status and severity chip
.alert           success and error message
.empty           empty state or placeholder panel
.stat            small labelled value tile
```

Severity and status chips for the planned repair queue already exist:

```text
.badge--high
.badge--medium
.badge--low
```

## Responsive Behaviour

The layout is expected to work on a phone, because crew employees will scan QR codes at the machine.

Breakpoints are defined in section 11 of the stylesheet. Feature templates should not add their own media queries for layout that the grid utilities already handle:

```text
.grid--2
.grid--3
.grid--4
```

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

The machines, repairs and logs Blueprints already exist as placeholders, so building those features means filling in the layers below them rather than creating new packages.

Associated business logic would live in:

```text
services/machine_service.py
services/repair_service.py
services/log_service.py
```

Associated database entities would live in:

```text
models/machine.py
models/repair_request.py
models/maintenance_log.py
```

Associated templates already exist and would be expanded in place:

```text
templates/machines/
templates/repairs/
templates/logs/
```

For a feature that does not yet have a Blueprint, create the package, register it in the application factory, add the matching template folder, and add its tab to:

```text
app/templates/partials/_topbar.html
```

This allows features to grow independently while following a common architecture.

---

# Primary Design Goals

RepRequest prioritizes:

```text
Manageable complexity
Clear module responsibilities
Consistent presentation
Company data isolation
Reusable business logic
Secure authorization
Ease of team development
Low merge-conflict risk
Testability
Future extensibility
```

New design decisions should support these goals whenever practical.