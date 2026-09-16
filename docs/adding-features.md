# Adding Features to RepRequest

This document explains the expected process for adding a new RepRequest feature.

Use these conventions unless the feature has a strong reason to require a different design.

---

# Example Feature: Machines

Suppose RepRequest needs machine management.

The feature may require:

```text
Machine database records
Machine business logic
Machine routes
Machine templates
Permissions
Tests
```

The recommended structure is:

```text
app/
├── machines/
│   ├── __init__.py
│   └── routes.py
│
├── models/
│   └── machine.py
│
├── services/
│   └── machine_service.py
│
└── templates/
    └── machines/
        ├── list.html
        ├── create.html
        └── detail.html
```

---

# Step 1 — Define the Data

If the feature requires persistent data, create or update a model.

Example:

```text
app/models/machine.py
```

The model should define:

```text
stored fields
relationships
entity-specific behavior
```

Avoid placing HTTP behavior inside a model.

After creating a new model, expose it through:

```text
app/models/__init__.py
```

---

# Step 2 — Create the Service Logic

Create:

```text
app/services/machine_service.py
```

Service functions should represent meaningful application operations.

Examples:

```python
create_machine(...)
get_company_machines(...)
get_company_machine(...)
update_machine(...)
delete_machine(...)
```

Company-owned data should always be scoped to a company.

Example:

```python
Machine.query.filter(
    Machine.id == machine_id,
    Machine.company_id == company_id
).first()
```

Services should not use:

```text
request.form
render_template
redirect
url_for
```

Those belong to routes.

---

# Step 3 — Create the Blueprint

Create:

```text
app/machines/
├── __init__.py
└── routes.py
```

Example:

```python
from flask import Blueprint

machines_bp = Blueprint(
    "machines",
    __name__,
    url_prefix="/machines"
)
```

Route functions should remain small.

A typical route should:

```text
Read request
Validate request
Check authorization
Call service
Return response
```

---

# Step 4 — Register the Blueprint

Add the new Blueprint in:

```text
app/__init__.py
```

Example:

```python
from app.machines.routes import machines_bp

app.register_blueprint(machines_bp)
```

---

# Step 5 — Add Authorization

Determine which roles may access the new functionality.

Reuse authorization helpers from:

```text
app/authorization.py
```

Example:

```python
@company_admin_required
```

If a genuinely reusable permission rule is needed, add it to the authorization module rather than defining duplicate authorization code inside the feature.

---

# Step 6 — Create Templates

Store templates under the feature name.

Example:

```text
app/templates/machines/
```

Use Blueprint endpoint names in `url_for()`.

Example:

```html
{{ url_for('machines.create_machine') }}
```

Do not use hidden buttons as the only authorization mechanism.

---

# Step 7 — Protect Company Ownership

Any company-owned resource must be retrieved using the authenticated user's company.

Example:

```python
machine = machine_service.get_company_machine(
    company_id=current_user.company_id,
    machine_id=machine_id
)
```

Do not trust:

```text
company_id from form data
company_id from an editable URL
company_id from hidden input
```

for access-control decisions.

---

# Step 8 — Handle Errors

Reusable application-wide HTTP errors belong in:

```text
app/errors.py
```

Business-rule errors may use service exceptions from:

```text
app/services/exceptions.py
```

Routes should translate service errors into appropriate user-facing responses.

---

# Step 9 — Test the Feature

At minimum, test:

```text
Expected successful behavior
Invalid input
Unauthorized users
Cross-company access
Duplicate or conflicting data
Direct URL manipulation
```

Automated testing conventions live under:

```text
tests/
```

after the testing framework is introduced.

---

# Step 10 — Review the Design

Before opening a pull request, ask:

```text
Does this feature have one clear responsibility?

Did business logic accidentally end up in a route?

Did HTTP behavior accidentally end up in a service?

Are role strings hard-coded?

Is authorization enforced server-side?

Is company-owned data scoped to current_user.company_id?

Does the new feature follow existing naming and directory conventions?

Could another developer understand where to modify this feature later?
```

If the answer to these questions is yes, the feature is likely following the intended RepRequest architecture.