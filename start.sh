#!/usr/bin/env bash
gunicorn mi_sitio_web.wsgi:application --bind 0.0.0.0:$PORT --workers 4