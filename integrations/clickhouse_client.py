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
                    database=self.config.get('DATABASE', 'default'),
                    secure=self.config.get('SECURE', False)
                )
                logger.info("ClickHouse connection established")
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

    def execute_command(self, command, params=None):
        """Execute a DDL or INSERT command that does not return a result set."""
        client = self.connect()
        try:
            client.command(command, parameters=params)
            return True
        except Exception as e:
            logger.error(f"ClickHouse command execution failed: {e}")
            return False

    def insert_row(self, table, data_dict):
        """Insert a single row into a ClickHouse table from a dictionary."""
        if not data_dict:
            return False
        columns = list(data_dict.keys())
        values = list(data_dict.values())
        col_str = ', '.join(columns)
        placeholders = ', '.join([f'%({c})s' for c in columns])
        query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"
        return self.execute_command(query, params=data_dict)

    def insert_dataframe(self, table, df):
        client = self.connect()
        try:
            client.insert_df(table, df)
            return True
        except Exception as e:
            logger.error(f"ClickHouse insert failed: {e}")
            return False
