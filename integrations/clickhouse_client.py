import clickhouse_connect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ClickHouseClient:
    def __init__(self):
        self.config = settings.CLICKHOUSE_SETTINGS
        self.client = None

    def connect(self):
        if not self.client:
            try:
                self.client = clickhouse_connect.get_client(
                    host=self.config.get('HOST', 'localhost'),
                    port=self.config.get('PORT', 8123),
                    username=self.config.get('USERNAME', 'default'),
                    password=self.config.get('PASSWORD', ''),
                    database=self.config.get('DATABASE', 'default')
                )
            except Exception as e:
                logger.error(f"Failed to connect to ClickHouse: {e}")
                raise e
        return self.client

    def execute_query(self, query, params=None):
        client = self.connect()
        try:
            return client.query(query, parameters=params)
        except Exception as e:
            logger.error(f"ClickHouse query execution failed: {e}")
            return None

    def insert_dataframe(self, table, df):
        client = self.connect()
        try:
            client.insert_df(table, df)
            return True
        except Exception as e:
            logger.error(f"ClickHouse insert failed: {e}")
            return False
