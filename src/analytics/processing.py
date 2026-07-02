import pandas as pd


def calculate_attrition_rate(df: pd.DataFrame) -> float:
    """
    Calculates the overall attrition rate from the DataFrame.
    """
    if df.empty or 'Attrition' not in df.columns:
        return 0.0
    return df['Attrition'].mean()

def get_department_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Provides a summary of average salary, average hours, and attrition rate by department.
    """
    if df.empty:
        return pd.DataFrame()
        
    summary = df.groupby('Department').agg({
        'Salary': 'mean',
        'MonthlyHours': 'mean',
        'Attrition': 'mean',
        'EmployeeID': 'count'
    }).rename(columns={'EmployeeID': 'Headcount'})
    
    # Format the metrics for better readability if needed
    summary['Salary'] = summary['Salary'].round(2)
    summary['MonthlyHours'] = summary['MonthlyHours'].round(1)
    summary['Attrition Rate (%)'] = (summary['Attrition'] * 100).round(2)
    
    return summary.sort_values(by='Attrition Rate (%)', ascending=False)
