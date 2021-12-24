#modelos para la conexion a las bases de datos
#pueden agregarse mas archivos si es necesario
from contextlib import closing
from os import environ
import psycopg2

class DbConnectionModel:
    DB_CONNECTION_PARMS = "dbname=bsmwzlwv7shc7knd1h5s user=ufem0pxjnrqgftesiygx password=KtmHVh8YaRu8JZpIT0hN host=bsmwzlwv7shc7knd1h5s-postgresql.services.clever-cloud.com port=5432"

    def __init__(self):
        self.connectiondb = None
        self.cursor = None
    
    def execute_sql_stmt(self, statement, values, is_query=False):
        try:
            result = None
            db_params = self.DB_CONNECTION_PARMS
            with closing(psycopg2.connect(db_params)) as connection:
                with closing(connection.cursor()) as cursor:
                    result = cursor.execute(statement, values)
                    if is_query:
                        result = cursor.fetchall()
                    connection.commit()
            return result
        except Exception as e:
            raise e