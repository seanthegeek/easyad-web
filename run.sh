#!/bin/bash

pkill gunicorn >/dev/null 2>&1
cd /home/easyad/easyad-web
/home/easyad/virtualenvs/adapi/bin/gunicorn -c gunicorn_config.py  adapi:app
