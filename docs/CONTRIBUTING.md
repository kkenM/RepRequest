# Contributing to RepRequest

This document defines the development workflow and coding conventions for the RepRequest team.

The goal is to keep the project organized, secure, and easy for multiple developers to work on at the same time.

---

# 1. Development Workflow

RepRequest uses feature branches and pull requests.

Do not develop new functionality directly on `main`.

Before starting new work:

```bash
git switch main
git pull origin main
git switch -c feature/your-feature-name
```

Examples:

```bash
git switch -c feature/machine-management
git switch -c feature/repair-requests
git switch -c fix/login-validation
git switch -c refactor/service-layer
```

After completing and testing the work:

```bash
git add -A
git commit -m "Describe the completed change"
git push -u origin feature/your-feature-name
```

Create a pull request into:

```text
main
```

The pull request should be reviewed before merging.

After the pull request is merged:

```bash
git switch main
git pull origin main
git branch -d feature/your-feature-name
```

Remote names are local Git aliases. Most clones use `origin`, but a developer may use another name.

---

# 2. Project Architecture

RepRequest separates code by responsibility.

The major layers are:

```text
Routes
    ↓
Services
    ↓
Models
    ↓
Database
```

Routes should not contain large amounts of database or business logic.

Services should not render HTML or depend on form requests.

Models define stored application data and behavior intrinsic to that data.

Templates control presentation but must never be relied upon for security.

See:

```text
docs/architecture.md
```

for the complete architecture.

---

# 3. Where Code Belongs

## Routes

Location:

```text
app/<feature>/routes.py
```

Routes should:

- receive HTTP requests
- read form or URL data
- perform basic request validation
- call service functions
- choose redirects or templates
- return HTTP responses

Routes should not contain complex database operations.

Example:

```python
employee = user_service.get_company_employee(
    company_id=current_user.company_id,
    employee_id=employee_id
)
```

---

## Services

Location:

```text
app/services/
```

Services contain application and business logic.

Examples:

```text
Create an employee
Update an employee
Delete an employee
Create a company
Assign a technician
Create a repair request
Change a repair status
```

Services may access models and the database.

Services should not:

```text
render templates
read request.form
redirect users
depend on HTML
```

---

## Models

Location:

```text
app/models/
```

Models define database entities.

Examples:

```text
Company
User
Machine
RepairRequest
```

A model may contain behavior that naturally belongs to that entity.

Examples:

```python
user.set_password(...)
user.check_password(...)
```

Business workflows involving multiple entities generally belong in a service instead.

---

## Templates

Location:

```text
app/templates/
```

Templates should be organized by feature.

Example:

```text
templates/
├── auth/
├── admin/
├── main/
├── machines/
└── repairs/
```

Templates control presentation.

Templates do not provide security.

Hiding a button is not the same as preventing access to its route.

---

## Authorization

Location:

```text
app/authorization.py
```

Reusable route permissions belong here.

Example:

```python
@company_admin_required
def create_employee():
    ...
```

Do not create separate authorization decorators inside individual Blueprint files unless there is a strong architectural reason.

---

## Roles

Location:

```text
app/roles.py
```

All application role values must be defined here.

Do not hard-code role strings throughout the project.

Bad:

```python
if user.role == "company-admin":
```

Preferred:

```python
if user.is_company_admin:
```

or:

```python
role=COMPANY_ADMIN
```

---

# 4. Security Rules

RepRequest is a multi-company application.

Company-owned resources must always be scoped to the authenticated user's company.

For example:

```python
employee = user_service.get_company_employee(
    company_id=current_user.company_id,
    employee_id=employee_id
)
```

Never trust a company ID submitted from the browser for authorization.

Bad:

```python
company_id = request.form["company_id"]
```

Preferred:

```python
company_id = current_user.company_id
```

A user must never be able to modify another company's resources by changing a URL, form field, or request manually.

Authorization must be enforced by Python routes or services, not only by HTML templates.

---

# 5. Passwords

Never store plaintext passwords.

Use the User model:

```python
user.set_password(password)
```

To verify a password:

```python
user.check_password(password)
```

Do not manually compare passwords or password hashes.

---

# 6. Configuration and Secrets

Secrets must not be committed to Git.

Examples:

```text
SECRET_KEY
database credentials
API keys
```

Local secret files such as `.env` must remain ignored by Git.

Configuration belongs in:

```text
config.py
```

---

# 7. Comments and Documentation

Comments should explain:

```text
WHY a decision exists
security requirements
important assumptions
non-obvious behavior
```

Avoid comments that merely repeat the code.

Poor comment:

```python
# Add user to database
db.session.add(user)
```

Useful comment:

```python
# SECURITY:
# company_id must come from the authenticated administrator
# rather than browser-submitted data to prevent cross-company access.
company_id=current_user.company_id
```

Public service functions and important route functions should have short docstrings explaining their responsibility.

---

# 8. Imports

Prefer imports from the public package interface.

Example:

```python
from app.models import Company, User
```

instead of importing individual model modules everywhere.

Role values should come from:

```python
from app.roles import ...
```

Authorization decorators should come from:

```python
from app.authorization import ...
```

---

# 9. Before Opening a Pull Request

Confirm that:

- the application starts successfully
- existing login/logout behavior still works
- authorization still works
- company data remains isolated
- the changed feature works
- unrelated behavior was not broken
- temporary print statements have been removed
- old or unused files have been removed
- secrets and database files are not staged
- code follows the existing architecture

The automated test suite will also be required after testing infrastructure is introduced.

---

# 10. Pull Request Scope

Keep pull requests focused.

Prefer:

```text
Add machine registration
```

over:

```text
Add machines, redesign login, change database structure,
rewrite CSS, and refactor repair requests
```

Smaller focused pull requests are easier to review and reduce merge conflicts.

---

# 11. Design Principle

When deciding where code belongs, ask:

```text
Is this responding to HTTP?
→ Route

Is this an application operation or business rule?
→ Service

Does this describe stored data?
→ Model

Is this controlling access?
→ Authorization

Is this defining a role?
→ roles.py

Is this presenting information?
→ Template
```

If responsibility is unclear, discuss the design before introducing a new architectural pattern.

# Database Migrations

RepRequest uses Flask-Migrate to manage database schema changes.

Do not rely on `db.create_all()` for normal application development.

After pulling code that includes new migrations, run:

```bash
python -m flask --app run.py db upgrade
```

When intentionally changing a database model:

```bash
python -m flask --app run.py db migrate -m "Describe schema change"
python -m flask --app run.py db upgrade
```

Always review generated migration files before committing them.

Migration files under:

```text
migrations/
```

must be committed to Git.

The local SQLite database under:

```text
instance/
```

must not be committed.

Do not create migrations for unrelated model changes in the same branch unless they belong to the same feature.