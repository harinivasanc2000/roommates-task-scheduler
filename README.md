# Roommate Task Scheduler

A shared, no-login Django app that creates a fair Monday–Sunday household rota. One roommate owns every task for a complete week, then the rota passes to the next active roommate alphabetically the following Monday. The first cycle begins on the upcoming Monday.

## What everyone can do

- View the current week and the following four weeks at once.
- Choose who you are when the site opens; Homeflow remembers the choice on that device and shows a personal character and greeting.
- See the rotating weekly house lead and a completion bar for every week.
- Tick chores off and leave shared notes on individual tasks.
- Move a task to another day within its assigned Monday–Sunday week so everyone sees the change.
- Use **Manage home** to add or pause roommates and chores—no admin account required.
- Switch between Pearl, Midnight, and Rose visual themes; the chosen theme stays on that device.
- Download only your own tasks from the five visible weeks as one `.ics` calendar file.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and use **Manage home** to add the four roommates. Starter chores are created by the first migration. Share this same URL after deploying the app to a public host.

Before production deployment, set `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` through secure configuration.
