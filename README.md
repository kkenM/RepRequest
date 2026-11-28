# RepRequest

RepRequest is a Flask web app for managing machine repair requests. Companies register, admins create employee accounts, and machines get QR labels that employees scan to report problems.

This README explains how to install and run the prototype on your own computer using only the source code. No hosting account is needed. Everything runs locally, and the database is a single SQLite file.

> **Prototype notice:** Use test data only. Do not enter real employee details.

---

## What you need first

| Requirement | How to check | Where to get it |
|---|---|---|
| Python 3.13 (newer is fine; the project was developed on 3.13) | `python --version` | https://www.python.org/downloads/ |
| Git | `git --version` | https://git-scm.com/downloads |
| A terminal | Terminal (macOS/Linux), PowerShell (Windows) | built in |

On macOS/Linux the Python command may be `python3` instead of `python`. If `python --version` fails or shows Python 2.x, use `python3` in every command below.

---

## Step 1. Get the source code

```bash
git clone https://github.com/kkenM/RepRequest.git
cd RepRequest
```

If you received the code as a ZIP file instead, unzip it, open a terminal, and `cd` into the folder that contains `run.py`.

**Check:** `ls` (macOS/Linux) or `dir` (Windows) should list `run.py`, an `app` folder, a `migrations` folder and a `docs` folder.

---

## Step 2. Create a virtual environment

A virtual environment keeps RepRequest's libraries separate from the rest of your computer.

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell says scripts are disabled, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Windows (Command Prompt)**
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**Check:** your prompt now starts with `(.venv)`. You must re-activate the environment (the `activate` line only) every time you open a new terminal.

---

## Step 3. Install the dependencies

```bash
pip install -r docs/requirements.txt
```

**Check:** the command finishes without a red `ERROR`. Running `pip list` should show Flask, Flask-SQLAlchemy and Flask-Migrate among others.

---

## Step 4. (Optional) Configure settings with a `.env` file

For a quick look at the app you can **skip this step**. The app starts with a built-in development secret key, which is fine on your own computer.

Create a file named `.env` in the project root (next to `run.py`) only if you want email to work, or want your own secret key:

```
SECRET_KEY=any-long-random-string

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-gmail-address
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=RepRequest <your-gmail-address>
```

Notes:

- **Do not** set `APP_ENV=production` or `SESSION_COOKIE_SECURE=1` for local use. Those are for the live server only; secure cookies will not work over plain `http://localhost`.
- The mail settings are used to email new employees their temporary password and to send password-reset links. Use a Gmail **app password** (Google Account → Security → 2-Step Verification → App passwords), never your real password.
- If mail is not configured, the app still runs, but those emails will not be delivered. The failure is logged in the terminal.
- `.env` is git-ignored. Never commit it.

---

## Step 5. Create the database

Run this **one** command from the project root. It builds every table from the code and records the database as up to date:

**macOS / Linux**
```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
flask --app run db stamp head
```

**Windows (PowerShell / Command Prompt):** the same two commands work as written.

> **Why not just `flask db upgrade`?** The first migration in the project does not create the base `company` and `user` tables, so `upgrade` fails on an empty database. Creating the tables directly and then "stamping" avoids that. After this, `flask db upgrade` works normally for any newer migrations.

**Check:**
```bash
flask --app run db current
```
should print a revision ID followed by `(head)`. A file `instance/accounts.db` now exists.

---

## Step 6. Run the app

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser (Flask's default port; if the terminal prints a different address, use that one). Leave the terminal open while you use the app. Press `Ctrl+C` to stop it.

---

## Step 7. Try it out (walkthrough)

1. Click **Register** and create a test company and admin account.
2. Sign in as that admin.
3. Create an employee from the admin page. The app generates a username and a temporary password for them.
4. Sign out, then sign in as the employee. You will be asked to change the temporary password.
5. As an admin, add a machine and open its QR label.
6. Try **Forgot password** and **Sign out of all devices** to see the session and reset flows.

---

## Running the tests

```bash
pip install pytest
pytest
```

All tests should pass. (If `pytest` is already in `docs/requirements.txt`, the install line does nothing harmful.)

---

## Resetting the database

To wipe all data and start fresh:

1. Stop the app (`Ctrl+C`).
2. Delete `instance/accounts.db`.
3. Repeat **Step 5**.

---

## Using the app from your phone (optional)

QR codes generated locally point at `localhost`, so a phone cannot open them. To test scanning:

1. Connect your phone and computer to the same Wi-Fi network.
2. Start the server so it listens on the network:
   ```bash
   flask --app run run --host 0.0.0.0
   ```
3. Find your computer's local IP address (e.g. `192.168.1.20`) and open `http://192.168.1.20:5000` on your phone.

QR labels will still encode `localhost` unless the app is configured with a different base URL, so for a real scan test the project is better deployed to a public host.

---

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `python: command not found` | Use `python3`, or reinstall Python and tick "Add Python to PATH" on Windows. |
| `ModuleNotFoundError: No module named 'flask'` | The virtual environment is not active. Re-run the activate line from Step 2, then retry. |
| `No such table: user` or `company` | Step 5 was skipped or run in the wrong folder. Run it from the folder containing `run.py`. |
| `flask db upgrade` fails on a new database | Expected. Use the Step 5 method instead. |
| `Address already in use` | Another program is using port 5000. Stop it, or run `flask --app run run --port 5001`. |
| `400 Bad Request: The CSRF token is missing` | A form is missing its hidden `csrf_token` field. Report which page it came from. |
| Login seems to "not stick" | Make sure `SESSION_COOKIE_SECURE=1` is **not** in your `.env` when using `http://`. |
| Emails never arrive | Check the `MAIL_*` values and that you used a Gmail app password. Errors appear in the terminal. |

---

## Project layout

```
RepRequest/
├── run.py              # Entry point for local development
├── app/                # Application code (routes, models, templates, static files)
├── migrations/         # Database migration history (Flask-Migrate / Alembic)
├── docs/
│   └── requirements.txt  # Python dependencies
├── instance/           # Local SQLite database (created in Step 5, git-ignored)
└── .env                # Your private settings (optional, git-ignored)
```

---

