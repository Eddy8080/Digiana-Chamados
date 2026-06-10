web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn setup.wsgi --bind 0.0.0.0:$PORT
