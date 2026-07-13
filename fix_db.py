import sqlite3
import pandas as pd

conn = sqlite3.connect('hr_data.db')
# We know the employees table is currently identical to the CSV, which has all columns.
df = pd.read_sql('SELECT * FROM employees', conn)

core_cols = ['EmployeeID', 'Tenure', 'Department', 'Role', 'MonthlyHours', 'LastPromotion', 'Salary', 'Attrition']
ml_cols = ['EmployeeID', 'RiskPercentage', 'Driver1', 'Driver2', 'Driver3']

emp_df = df[[c for c in core_cols if c in df.columns]]
ml_df = df[[c for c in ml_cols if c in df.columns]]

emp_df.to_sql('employees', conn, if_exists='replace', index=False)
ml_df.to_sql('attrition_scores', conn, if_exists='replace', index=False)
conn.close()
print("Fixed DB!")
