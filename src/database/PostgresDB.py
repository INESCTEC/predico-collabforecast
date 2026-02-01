import pandas as pd

from sqlalchemy import create_engine, text

from .helpers import to_sql_no_update


class PostgresDB:
    instances = {}

    def __init__(self, config_name):
        from conf import settings
        db_cfg = settings.DATABASES[config_name]
        self.engine = create_engine(f"postgresql://"
                                    f"{db_cfg['USER']}:{db_cfg['PASSWORD']}@"
                                    f"{db_cfg['HOST']}:{db_cfg['PORT']}/"
                                    f"{db_cfg['NAME']}")

    @staticmethod
    def get_db_instance(config_name="default"):
        if PostgresDB.instances.get(config_name, None) is None:
            PostgresDB.instances[config_name] = PostgresDB(
                config_name=config_name
            )
        return PostgresDB.instances[config_name]

    def execute_query(self, query):
        with self.engine.connect() as con:
            rs = con.execute(text(query))
        return rs

    def read_query_pandas(self, query):
        return pd.read_sql_query(query, con=self.engine)

    def insert_dataframe(self, df, table, force_update=False):
        connection = self.engine.raw_connection()
        return to_sql_no_update(conn=connection, df=df, table=table)

    def test_connection(self):
        try:
            with self.engine.connect():
                return True
        except Exception:
            return False

if __name__ == '__main__':
    import datetime as dt
    db = PostgresDB(config_name="default")
    data = db.read_query_pandas("select * from raw_data "
                                "where resource_id='bob-asd-3-23';")
    forecasts = data[["datetime", "value", "unit", "registered_at", "user_id",
                      "resource_id"]]
    forecasts["market_session_id"] = 1
    forecasts["request"] = dt.datetime.now()
    db.insert_dataframe(df=forecasts, table="market_forecasts")
