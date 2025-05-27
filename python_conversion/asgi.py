import os
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from python_conversion.app import app as flask_app

os.environ.setdefault('FLASK_ENV', 'development')

fastapi_app = FastAPI()

# Mount the Flask app as WSGI middleware
fastapi_app.mount("/", WSGIMiddleware(flask_app))
