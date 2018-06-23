# -*- coding:utf-8 -*-

from bintest import app
from controllers import IndexViewController
from controllers import GetLatestPriceController
from controllers import GetChartDataController


@app.route("/")
def index():
    return IndexViewController().call()


@app.route("/price/<symbol>")
def get_latest_price(symbol):
    return GetLatestPriceController().call(symbol)


@app.route("/chart/<symbol>")
def get_chart_data(symbol):
    return GetChartDataController().call(symbol)
