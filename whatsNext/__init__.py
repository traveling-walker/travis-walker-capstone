from flask import Flask
from flask_caching import Cache


app = Flask(__name__)

cache = Cache()

cache.init_app(app=app, config={
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": '/tmp',
    "CACHE_DEFAULT_TIMEOUT": 0
})

import whatsNext.views
