import sqlite3
from pathlib import Path
from typing import Optional, Sequence, Union

import joblib
import numpy as np
import pandas as pd
import shap

REQUIRED_FEATURE_COLS = [
    "EmployeeID",
    "Tenure",
    "Department",
    "Role",
    "MonthlyHours",
    "LastPromotion",
    "Salary",
]


def _project_root() -> Path:
    return Path(__file__).parent.parent.parent


def default_db_path() -> Path:
    return _project_root() / "hr_data.db"


def default_model_path() -> Path:
    return _project_root() / "models" / "attrition_model.pkl"


def load_model(model_path: Optional[Union[str, Path]] = None) -> dict:
    """Load the trained attrition model and its expected feature columns."""
    path = Path(model_path) if model_path else default_model_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run `python -m src.models.training` first."
        )
    saved = joblib.load(path)
    if "model" not in saved or "features" not in saved:
        raise ValueError(f"Invalid model artifact at {path}: expected keys 'model' and 'features'.")
    return saved


def validate_employee_frame(df: pd.DataFrame) -> None:
    """Ensure the roster has the columns required for inference."""
    missing = [c for c in REQUIRED_FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            "Uploaded roster is missing required columns for scoring: "
            + ", ".join(missing)
        )


def score_dataframe(
    df: pd.DataFrame,
    model=None,
    expected_features: Optional[Sequence[str]] = None,
    model_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    Run XGBoost risk scoring + SHAP top-3 drivers on an employee roster DataFrame.

    Returns a DataFrame with columns:
    EmployeeID, RiskPercentage, Driver1, Driver2, Driver3
    """
    validate_employee_frame(df)

    if model is None or expected_features is None:
        saved = load_model(model_path)
        model = saved["model"]
        expected_features = saved["features"]

    work = df.copy()
    cols_to_drop = ["EmployeeID"]
    if "Attrition" in work.columns:
        cols_to_drop.append("Attrition")
    # Drop any pre-baked score/driver columns so they never leak into features
    for extra in ("RiskPercentage", "Driver1", "Driver2", "Driver3",
                  "TopDriver1", "TopDriver2", "TopDriver3"):
        if extra in work.columns:
            cols_to_drop.append(extra)

    X = work.drop(columns=[c for c in cols_to_drop if c in work.columns])
    feature_cols = [c for c in REQUIRED_FEATURE_COLS if c != "EmployeeID"]
    X = X[feature_cols]

    X_encoded = pd.get_dummies(X, columns=["Department", "Role"], dtype=int)
    X_aligned = X_encoded.reindex(columns=list(expected_features), fill_value=0)

    probs = model.predict_proba(X_aligned)[:, 1]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_aligned)

    feature_names = np.array(list(expected_features))
    driver1_list, driver2_list, driver3_list = [], [], []

    for i in range(len(X_aligned)):
        if isinstance(shap_values, list):
            sv = shap_values[1][i]
        else:
            sv = shap_values[i]
        abs_sv = np.abs(sv)
        top_indices = np.argsort(abs_sv)[::-1][:3]
        top_features = feature_names[top_indices]
        driver1_list.append(top_features[0] if len(top_features) > 0 else None)
        driver2_list.append(top_features[1] if len(top_features) > 1 else None)
        driver3_list.append(top_features[2] if len(top_features) > 2 else None)

    return pd.DataFrame(
        {
            "EmployeeID": work["EmployeeID"].astype(str),
            "RiskPercentage": np.round(probs * 100, 2),
            "Driver1": driver1_list,
            "Driver2": driver2_list,
            "Driver3": driver3_list,
        }
    )


def persist_employees(
    emp_df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
) -> None:
    """Replace the employees table with the given roster (core columns only)."""
    path = Path(db_path) if db_path else default_db_path()
    core_cols = [
        "EmployeeID",
        "Tenure",
        "Department",
        "Role",
        "MonthlyHours",
        "LastPromotion",
        "Salary",
        "Attrition",
    ]
    out = emp_df[[c for c in core_cols if c in emp_df.columns]].copy()
    if "Attrition" not in out.columns:
        out["Attrition"] = 0
    with sqlite3.connect(path) as conn:
        out.to_sql("employees", conn, if_exists="replace", index=False)


def persist_scores(
    scores_df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
) -> None:
    """Replace the attrition_scores table."""
    path = Path(db_path) if db_path else default_db_path()
    cols = ["EmployeeID", "RiskPercentage", "Driver1", "Driver2", "Driver3"]
    out = scores_df[cols].copy()
    with sqlite3.connect(path) as conn:
        out.to_sql("attrition_scores", conn, if_exists="replace", index=False)


def ingest_and_score(
    roster_df: pd.DataFrame,
    db_path: Optional[Union[str, Path]] = None,
    model_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    Persist a fresh employee roster and score it live with the saved XGBoost model + SHAP.

    Always recomputes RiskPercentage / drivers from the model (ignores any pre-baked
    score columns in the upload).
    """
    path = Path(db_path) if db_path else default_db_path()
    validate_employee_frame(roster_df)
    persist_employees(roster_df, path)
    scores = score_dataframe(roster_df, model_path=model_path)
    persist_scores(scores, path)
    return scores


def run_explainability_pipeline(
    db_path: Optional[Union[str, Path]] = None,
    model_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Batch-score all employees currently in the SQLite DB (CLI / offline use)."""
    path = Path(db_path) if db_path else default_db_path()
    print(f"Loading data from {path}...")
    with sqlite3.connect(path) as conn:
        df = pd.read_sql_query("SELECT * FROM employees", conn)

    print("Scoring with XGBoost + SHAP...")
    scores = score_dataframe(df, model_path=model_path)
    persist_scores(scores, path)
    print(f"Saved {len(scores)} scores to {path}.")
    return scores


def main():
    run_explainability_pipeline()
    print("Explainability pipeline completed successfully.")


if __name__ == "__main__":
    main()
