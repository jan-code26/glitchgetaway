# GlitchGetaway

An educational puzzle escape room Django application.

## Cursor Cloud specific instructions

### Architecture

Single-service Django 5.2 app with embedded SQLite3 database. No external services (no Redis, Postgres, Docker, etc.) required.

### Running the application

Standard commands per the README:

```bash
python3 manage.py migrate
python3 manage.py loaddata escape_rooms.json
python3 manage.py runserver 0.0.0.0:8000
```

- Health check: `GET /healthz/` returns `{"status": "ok"}`
- The `wsgi.py` auto-runs migrations and loads fixtures if the DB is empty, but for dev use `manage.py` directly.

### Linting / checks

```bash
python3 manage.py check
```

There is no dedicated linter (no flake8/ruff/mypy config). Django system check is the closest equivalent.

### Tests

```bash
python3 manage.py test
```

The test suite is currently empty (`escape/tests.py` has no test cases).

### Gotchas

- `STATICFILES_STORAGE` uses `whitenoise.storage.CompressedManifestStaticFilesStorage`. Run `python3 manage.py collectstatic --noinput` after changing static files or you'll get 500 errors on static asset references.
- The admin terminal is accessed in-app by typing `sudo login admin123` in the puzzle input field (not Django admin at `/admin/`).
- Session state (current room, attempts) is stored in Django sessions. Clearing cookies or flushing the session resets progress.
