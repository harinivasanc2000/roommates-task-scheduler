# Homeflow — Roommate Task Scheduler

Homeflow is a mobile-first Django web app for managing a shared Monday–Sunday household rota. One roommate owns the complete rota for a week, then responsibility passes to the next active roommate alphabetically.





## Features

- Five-week calendar covering the selected week and following four weeks.
- One clearly identified owner for every Monday–Sunday week.
- Editable alphabetical rotation starting date and person.
- Personal identity picker remembered in the browser session.
- Personal greetings, characters, and highlighted rota weeks.
- Clear task completion buttons and weekly progress bars.
- Three task-specific, personality-aware celebration messages per chore and roommate; repeat completions rotate to a different line.
- Shared task notes and rescheduling within the assigned week.
- Session-enforced ownership: the selected roommate can only complete, move, or annotate tasks assigned to them.
- Whole-week swap requests with recipient notifications and explicit accept or decline.
- Personal `.ics` downloads containing only the selected roommate's tasks.
- Public household management—no Django admin account required.
- Add, pause, and reactivate roommates and chores from the website.
- Pearl, Midnight, and Rose themes, custom accent colours, and calendar density options.
- Mobile swipe navigation, large touch controls, sticky navigation, and bottom-sheet dialogs.
- PostgreSQL, Gunicorn, WhiteNoise, secure environment settings, and Render deployment support.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The starter chores and household profiles are created by database migrations.

## Test

```bash
python manage.py check
python manage.py test
```

## Deploy

The repository contains a Render Blueprint, production build script, PostgreSQL support, and environment-based security settings. Follow [DEPLOYMENT.md](DEPLOYMENT.md) to publish it.

Never commit `.env`, database credentials, `SECRET_KEY`, `db.sqlite3`, or the local `.venv` directory.

## Change history

Project changes are recorded in [CHANGELOG.md](CHANGELOG.md). It is append-only: previous release entries remain unchanged, and each new release is added after the existing history.
