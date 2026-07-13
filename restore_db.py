import sqlite3
import pandas as pd

new_df = pd.read_csv("synthetic_hr_roster_1000.csv")
conn = sqlite3.connect('hr_data.db')

core_cols = ['EmployeeID', 'Tenure', 'Department', 'Role', 'MonthlyHours', 'LastPromotion', 'Salary', 'Attrition']
emp_df = new_df[[c for c in core_cols if c in new_df.columns]]
emp_df.to_sql('employees', conn, if_exists='replace', index=False)

ml_cols = ['EmployeeID', 'RiskPercentage', 'Driver1', 'Driver2', 'Driver3']
ml_df = new_df[[c for c in ml_cols if c in new_df.columns]]
ml_df.to_sql('attrition_scores', conn, if_exists='replace', index=False)

conn.close()
print("Restored!")
