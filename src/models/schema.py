from pydantic import BaseModel, Field


class EmployeeRecord(BaseModel):
    """
    Pydantic model for validating synthetic HR dataset records.
    Strictly typed fields for attrition modeling.
    """
    EmployeeID: str = Field(..., description="Unique anonymized identifier for the employee, e.g., EMP001")
    Tenure: int = Field(..., ge=0, description="Tenure in months")
    Department: str = Field(..., description="Department name")
    Role: str = Field(..., description="Role/Job title")
    MonthlyHours: int = Field(..., ge=0, description="Average monthly hours worked")
    LastPromotion: int = Field(..., ge=0, description="Months since last promotion")
    Salary: float = Field(..., ge=0.0, description="Annual salary in USD")
    Attrition: int = Field(..., ge=0, le=1, description="Binary attrition label: 1 if left, 0 if retained")
