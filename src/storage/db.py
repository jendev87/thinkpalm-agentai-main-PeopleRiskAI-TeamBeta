import sqlite3
from typing import List

import pandas as pd

from src.models.schema import EmployeeRecord


class HRDatabase:
    """
    Handles SQLite database connections, table creation, and data ingestion.
    """
    def __init__(self, db_path: str = "hr_data.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initializes the SQLite database with the required schema."""
        query = """
        CREATE TABLE IF NOT EXISTS employees (
            EmployeeID TEXT PRIMARY KEY,
            Tenure INTEGER,
            Department TEXT,
            Role TEXT,
            MonthlyHours INTEGER,
            LastPromotion INTEGER,
            Salary REAL,
            Attrition INTEGER
        );
        """
        query_scores = """
        CREATE TABLE IF NOT EXISTS attrition_scores (
            EmployeeID TEXT PRIMARY KEY,
            RiskPercentage REAL,
            TopDriver1 TEXT,
            TopDriver2 TEXT,
            TopDriver3 TEXT,
            FOREIGN KEY(EmployeeID) REFERENCES employees(EmployeeID)
        );
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            cursor.execute(query_scores)
            conn.commit()
            
    def ingest_records(self, records: List[EmployeeRecord]):
        """Ingests a list of Pydantic EmployeeRecord models into the database."""
        query = """
        INSERT OR REPLACE INTO employees 
        (EmployeeID, Tenure, Department, Role, MonthlyHours, LastPromotion, Salary, Attrition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        data = [
            (
                r.EmployeeID, 
                r.Tenure, 
                r.Department, 
                r.Role, 
                r.MonthlyHours, 
                r.LastPromotion, 
                r.Salary, 
                r.Attrition
            ) for r in records
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data)
            conn.commit()
            
    def load_to_dataframe(self) -> pd.DataFrame:
        """Loads the entire employees table into a Pandas DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("SELECT * FROM employees", conn)
        return df

    def ingest_attrition_scores(self, scores_df: pd.DataFrame):
        """Ingests a Pandas DataFrame of attrition scores into the database."""
        query = """
        INSERT OR REPLACE INTO attrition_scores 
        (EmployeeID, RiskPercentage, TopDriver1, TopDriver2, TopDriver3)
        VALUES (?, ?, ?, ?, ?)
        """
        data = scores_df[['EmployeeID', 'RiskPercentage', 'TopDriver1', 'TopDriver2', 'TopDriver3']].values.tolist()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(query, data)
            conn.commit()
