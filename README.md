# Deploy

## 1. No debug

Make sure `debug = False`  in `cmt_manager/settings.py`

## 2. Allowed hosts

Adapt `ALLOWED_HOSTS` according to your needs (this is list of host that the
server is allowed to serve on. It should agree or match with the --bind option
below)

## 3. Generate secure key

    python generate-secret-key.py

And put the key in the `cmt_manager/settings.py` file, for the `SECRET_KEY`
variable.

## 4. Migrate database

    virtualenv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py check --deploy # should only complain about SSL
    python manage.py migrate
    deactivate

## 5. Run

    .venv/bin/python -m daphne --bind <ipaddress> --port <port> cmt_manager.asgi:application

## 6. Fetch all the probes

Visit `/cmt/fetch-probes-checks`. Be careful, it can't do better than assume
that the `max_alert_level`, `enable` and `enable_pager` keys, you have to update
them manually.