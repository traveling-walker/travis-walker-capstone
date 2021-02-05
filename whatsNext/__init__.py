from flask import Flask
from common import cache

app = Flask(__name__)

cache.init_app(app=app, config={
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": '/tmp',
    "CACHE_DEFAULT_TIMEOUT": 0
})

import whatsNext.views