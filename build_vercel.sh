#!/usr/bin/env bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
