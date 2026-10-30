web: /app/.venv/bin/python manage.py migrate --noinput && /app/.venv/bin/python manage.py collectstatic --noinput && /app/.venv/bin/gunicorn cafeteria.wsgi:application --bind 0.0.0.0:$PORT
