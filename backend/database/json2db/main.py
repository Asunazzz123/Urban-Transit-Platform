import json
import sqlite3
from typing import Any, Dict, List
from backend.utils.constant import METRO_JSON_DIR

class connectDB:    
    def __init__(self, db_name: str):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
    def check_connector(fun):
        def wrapper(self, *args, **kwargs):
            if self.connection is None:
                raise ConnectionError("Database connection is not established.")
            return fun(self, *args, **kwargs)
        return wrapper
    @check_connector
    def execute(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        self.connection.commit()
    @check_connector
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
class MetroTransfer:
    def __init__(self,city_name : str, db_name:str):
        self.city_name = city_name
        self.db_name = db_name
        self.db = connectDB(db_name)

    def load_json(self):
        file_path = METRO_JSON_DIR / f'{self.city_name}_metro_transfer.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    
    def SQLorder(self):
        if self.db_name == "STATIONS":
            return f'''
            INSERT INTO STATIONS ()
            '''