import random
from typing import List

import numpy as np

from src.models.schema import EmployeeRecord

DEPARTMENTS = ["Engineering", "Sales", "HR", "Marketing", "Finance", "Operations"]
ROLES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Staff Engineer", "Engineering Manager"],
    "Sales": ["Sales Representative", "Account Executive", "Sales Manager", "VP of Sales"],
    "HR": ["HR Generalist", "Recruiter", "HR Manager", "VP of HR"],
    "Marketing": ["Marketing Specialist", "Growth Hacker", "Marketing Manager", "VP of Marketing"],
    "Finance": ["Financial Analyst", "Accountant", "Finance Manager", "VP of Finance"],
    "Operations": ["Operations Specialist", "Operations Manager", "Director of Operations"]
}

def generate_synthetic_data(num_records: int = 1000) -> List[EmployeeRecord]:
    """
    Generates a list of synthetic employee records using numpy and random.
    Validates each record using the EmployeeRecord Pydantic model.
    """
    np.random.seed(42)  # For reproducibility
    random.seed(42)

    records = []
    
    for i in range(1, num_records + 1):
        emp_id = f"EMP{i:04d}"
        
        department = random.choice(DEPARTMENTS)
        role = random.choice(ROLES[department])
        
        # Correlate some features loosely
        tenure = int(np.random.gamma(shape=2.0, scale=24.0))  # Months, right-skewed
        last_promotion = int(np.random.uniform(0, min(tenure + 1, 60)))
        
        # Base salary logic based on role seniority loosely
        base_sal = 60000
        if "Senior" in role or "Manager" in role:
            base_sal += 40000
        if "Staff" in role or "Director" in role:
            base_sal += 80000
        if "VP" in role:
            base_sal += 120000
        
        salary = round(np.random.normal(loc=base_sal, scale=base_sal * 0.1), 2)
        salary = max(30000.0, salary)
        
        monthly_hours = int(np.random.normal(loc=160, scale=20))
        monthly_hours = max(40, min(monthly_hours, 300))
        
        # Simple logistic-like probability for attrition based on features
        # Higher hours, lower salary, longer time since promotion -> higher attrition
        score = (monthly_hours - 160) * 0.05 - (salary - base_sal) * 0.0001 + (last_promotion - 12) * 0.1
        prob = 1 / (1 + np.exp(-score * 0.1 - 2.5)) # Base prob around 0.07-0.15
        
        attrition = 1 if np.random.random() < prob else 0
        
        # Validate through Pydantic
        record = EmployeeRecord(
            EmployeeID=emp_id,
            Tenure=tenure,
            Department=department,
            Role=role,
            MonthlyHours=monthly_hours,
            LastPromotion=last_promotion,
            Salary=salary,
            Attrition=attrition
        )
        records.append(record)
        
    return records

if __name__ == "__main__":
    data = generate_synthetic_data(5)
    for row in data:
        print(row.model_dump_json(indent=2))
    print("\nSuccessfully generated 5 sample records. Use generate_synthetic_data(1000) for full dataset.")
