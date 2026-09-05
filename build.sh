#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# أمر إنشاء المسؤول تلقائياً (سيتم يتجاهل الأمر إذا كان الحساب موجوداً بالفعل)
python manage.py createsuperuser --noinput || true