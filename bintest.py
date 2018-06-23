# -*- coding:utf-8 -*-

import os
import logging
import config
from flask import Flask
from misc import Log

app = Flask(__name__)

if not os.path.exists("logs"):
    os.mkdir("logs")

file_handler = logging.FileHandler(config.log_config.get("filename"))
file_handler.setLevel(config.log_config.get("level"))
file_handler.setFormatter(config.log_config.get("format"))

log = Log(file_handler, "Binance")
log.info("Binance service started.")

import views
