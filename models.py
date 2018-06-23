# -*- coding:utf-8 -*-

from peewee import (Model, TextField, DoubleField, DateTimeField, datetime as peewee_datetime)
from playhouse.pool import PooledPostgresqlExtDatabase


from config import db_config


binance_db = PooledPostgresqlExtDatabase(**db_config)
binance_db.commit_select = True
binance_db.autorollback = True


class BaseModel(Model):
    class Meta:
        database = binance_db


class PriceLog(BaseModel):
    class Meta:
        db_table = "price_logs"

    created = DateTimeField(default=peewee_datetime.datetime.now)
    symbol = TextField()
    max_price = DoubleField()
    min_price = DoubleField()
    drop_percent = DoubleField()


def init_db():
    try:
        binance_db.connect()
        table_list = [PriceLog]
        [binance_db.drop_tables(table_list)]
        print("Tables dropped.")

        [binance_db.create_tables(table_list)]
        print("Tables created.")
    except Exception:
        binance_db.rollback()
        raise


if __name__ == "__main__":
    init_db()
