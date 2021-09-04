web: python longterm/manage.py runserver 0.0.0.0:$PORT
worker1: celery -A longterm worker --pool=solo -l info -Q scraper
worker2: celery worker -l info -Q default -B
