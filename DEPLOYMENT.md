# Put Homeflow online with Render

The repository already includes Gunicorn, PostgreSQL support, WhiteNoise static-file serving, production security settings, and `build.sh`.

## Fastest route: Blueprint

1. Sign in to [Render](https://dashboard.render.com/) with GitHub and allow access to the private repository.
2. Open **Blueprints**, choose **New Blueprint Instance**, and select this repository.
3. Render reads `render.yaml`, creates Homeflow plus PostgreSQL, and generates the secret automatically.
4. Apply the Blueprint and wait for the generated `.onrender.com` address.

## Manual route

1. Create a PostgreSQL database in the same Render region as the web service.
2. Create a **Web Service**, connect this GitHub repository, and select Python.
4. Use `./build.sh` as the build command.
5. Use `gunicorn roommate_scheduler.wsgi:application` as the start command.
6. Add these environment variables:
   - `DEBUG=False`
   - `SECRET_KEY`: generate a long random value in Render.
   - `DATABASE_URL`: use the PostgreSQL database's internal URL.
   - `ALLOWED_HOSTS`: the hostname only, such as `homeflow-abcd.onrender.com`.
   - `CSRF_TRUSTED_ORIGINS`: the full HTTPS origin, such as `https://homeflow-abcd.onrender.com`.
6. Deploy and open the generated `.onrender.com` URL.

After that, each push to `main` can deploy automatically. Use a persistent PostgreSQL plan before relying on the app's task history; local SQLite files on a normal web service do not survive deployments.

## Availability and free-tier limits

Your own computer does not need to stay on; Render runs the application from its servers. On Render's Free plan, the web service sleeps after 15 minutes without traffic and the first visitor may wait about a minute while it wakes. The Free PostgreSQL database expires after 30 days.

For dependable household use, upgrade the PostgreSQL database to a persistent paid plan. If you also want immediate responses at all times, upgrade the web service from Free to a paid compute plan. GitHub pushes can still deploy automatically on either plan.

## Production checklist

- Keep `.env` and database credentials out of Git.
- Enable database backups before the rota contains important history.
- Add a custom domain only after the Render URL works.
- Run `python manage.py check --deploy` when changing production settings.
- Test identity selection, completion, rescheduling, and ICS downloads after every deployment.
