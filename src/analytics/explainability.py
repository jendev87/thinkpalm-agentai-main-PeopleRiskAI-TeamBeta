import sqlite3
import pandas as pd
import xgboost as xgb
import shap
import numpy as np
import joblib
from pathlib import Path

def main():
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / 'hr_data.db'
    model_path = project_root / 'models' / 'attrition_model.pkl'

    print(f"Loading data from {db_path}...")
    # Load data from database
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM employees", conn)
    
    print(f"Loading model from {model_path}...")
    # Load the trained model and expected features
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}. Please run training.py first.")
        return
        
    saved_data = joblib.load(model_path)
    model = saved_data['model']
    expected_features = saved_data['features']
    
    # Preprocessing
    print("Preprocessing data for inference...")
    # Drop target and identifier if they exist
    cols_to_drop = ['EmployeeID']
    if 'Attrition' in df.columns:
        cols_to_drop.append('Attrition')
        
    X = df.drop(columns=cols_to_drop)
    
    # One-hot encoding
    X_encoded = pd.get_dummies(X, columns=['Department', 'Role'], dtype=int)
    
    # Align features with training set
    X_aligned = X_encoded.reindex(columns=expected_features, fill_value=0)
    
    # Inference
    print("Calculating risk probabilities...")
    # Predict probability of class 1 (Attrition)
    probs = model.predict_proba(X_aligned)[:, 1]
    
    # SHAP Explainability
    print("Calculating SHAP values...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_aligned)
    
    # Extract top 3 drivers for each employee
    print("Extracting top impact drivers...")
    driver1_list = []
    driver2_list = []
    driver3_list = []
    
    feature_names = np.array(expected_features)
    
    for i in range(len(X_aligned)):
        # Get absolute SHAP values for the current employee
        # Note: Depending on xgboost version/objective, shap_values might be 2D (num_samples, num_features)
        # or a list. For standard binary classification with XGBoost, it's typically 2D.
        # We take the absolute values to find the most impactful features (positive or negative).
        if isinstance(shap_values, list):
            sv = shap_values[1][i]  # Use class 1 shap values if it's a list
        else:
            sv = shap_values[i]
            
        abs_sv = np.abs(sv)
        
        # Get indices of top 3 features (sorted in descending order)
        top_indices = np.argsort(abs_sv)[::-1][:3]
        top_features = feature_names[top_indices]
        
        # In case we have fewer than 3 features for some reason
        d1 = top_features[0] if len(top_features) > 0 else None
        d2 = top_features[1] if len(top_features) > 1 else None
        d3 = top_features[2] if len(top_features) > 2 else None
        
        driver1_list.append(d1)
        driver2_list.append(d2)
        driver3_list.append(d3)
        
    # Create the results dataframe
    print("Preparing results table...")
    df_scores = pd.DataFrame({
        'EmployeeID': df['EmployeeID'],
        'RiskPercentage': np.round(probs * 100, 2),
        'Driver1': driver1_list,
        'Driver2': driver2_list,
        'Driver3': driver3_list
    })
    
    # Save to SQLite database
    print(f"Saving scores to {db_path}...")
    with sqlite3.connect(db_path) as conn:
        df_scores.to_sql('attrition_scores', conn, if_exists='replace', index=False)
        
    print("Explainability pipeline completed successfully.")

if __name__ == '__main__':
    main()
