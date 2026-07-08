import pandas as pd
import numpy as np

def generate_synthetic_hr_roster(num_employees=1000):
    # Removed seed to allow varied data generation
    
    # Generate sequential Employee IDs matching your exact corporate format
    employee_ids = [f"EMP{i:04d}" for i in range(1, num_employees + 1)]
    
    # Explicit mapping of departments and valid role profiles from your schema
    dept_role_mapping = {
        "Engineering": ["Software Engineer", "Senior Engineer", "Staff Engineer", "Engineering Manager"],
        "Operations": ["Operations Specialist", "Operations Manager", "Director of Operations"],
        "Finance": ["Accountant", "Financial Analyst", "Finance Manager", "VP of Finance"],
        "Marketing": ["Marketing Specialist", "Growth Hacker", "Marketing Manager", "VP of Marketing"],
        "Sales": ["Sales Representative", "Account Executive", "Sales Manager", "VP of Sales"],
        "HR": ["Recruiter", "HR Generalist", "HR Manager", "VP of HR"]
    }
    
    departments = list(dept_role_mapping.keys())
    
    data = []
    drivers_pool = ["Tenure", "Salary", "MonthlyHours", "LastPromotion", "Role Overload", "Market Competitiveness"]
    
    for emp_id in employee_ids:
        # Pick a department and a logically assigned role
        dept = np.random.choice(departments)
        role = np.random.choice(dept_role_mapping[dept])
        
        # Tenure distribution in months (up to ~10 years)
        tenure = int(np.random.exponential(scale=36)) + 1
        
        # Monthly Hours centered around normal 160-180 baseline with variance
        monthly_hours = int(np.random.normal(loc=174, scale=15))
        monthly_hours = max(100, min(monthly_hours, 240)) # Cap boundaries
        
        # Months elapsed since last structured promotion line
        last_promotion = int(np.random.randint(0, min(tenure, 60)))
        
        # Generate appropriate corporate salary bounds based on organizational seniority tiers
        if "VP" in role or "Director" in role:
            salary = round(np.random.uniform(140000, 210000), 2)
        elif "Manager" in role or "Staff" in role:
            salary = round(np.random.uniform(95000, 135000), 2)
        elif "Senior" in role:
            salary = round(np.random.uniform(80000, 110000), 2)
        else:
            salary = round(np.random.uniform(50000, 78000), 2)
            
        # Binary structural classification flag (Historical historical turnover)
        attrition = np.random.choice([0, 1], p=[0.84, 0.16])
        
        # Generate a continuous AI predictive risk gradient (0% - 100%)
        # Intentionally skewing risk upward for low salary, high hours, and high tenure
        risk_base = 40.0
        if monthly_hours > 190: risk_base += 20.0
        if salary < 65000: risk_base += 15.0
        if tenure > 48 and last_promotion > 36: risk_base += 15.0
        
        risk_percentage = round(max(5.0, min(risk_base + np.random.normal(0, 10), 99.9)), 1)
        
        # Deduplicate and prioritize primary attrition triggers
        shuffled_drivers = list(np.random.choice(drivers_pool, size=3, replace=False))
        # Ensure tenure and salary surface highly if conditions match your dashboard analysis
        if tenure > 48 and "Tenure" not in shuffled_drivers: shuffled_drivers[0] = "Tenure"
        if salary < 65000 and "Salary" not in shuffled_drivers: shuffled_drivers[1] = "Salary"
        
        data.append({
            "EmployeeID": emp_id,
            "Tenure": tenure,
            "Department": dept,
            "Role": role,
            "MonthlyHours": monthly_hours,
            "LastPromotion": last_promotion,
            "Salary": salary,
            "Attrition": attrition,
            "RiskPercentage": risk_percentage,
            "Driver1": shuffled_drivers[0],
            "Driver2": shuffled_drivers[1],
            "Driver3": shuffled_drivers[2]
        })
        
    return pd.DataFrame(data)

# Generate and build output paths
df_mock = generate_synthetic_hr_roster(1250)
df_mock.to_csv("/Users/thinkpalm/Desktop/Training/Main Project/SampleData/synthetic_hr_roster_1250.csv", index=False)
print(f"Success! Generated a matching manifest with shape: {df_mock.shape}")