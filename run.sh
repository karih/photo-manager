#!/bin/bash

# Runs gunicorn instance

gunicorn -b 127.0.0.1:8000 pm:app
