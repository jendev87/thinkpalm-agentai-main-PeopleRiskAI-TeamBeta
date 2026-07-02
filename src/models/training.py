import sqlite3
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from pathlib import Path
import os

def main():
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / 'hr_data.db'
    model_dir = project_root / 'models'
    model_dir.mkdir(exist_ok=True)
    model_path = model_dir / 'attrition_model.pkl'

    print(f"Loading data from {db_path}...")
    # Load data from database
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM employees", conn)
    
    # Preprocessing
    print("Preprocessing data...")
    X = df.drop(columns=['EmployeeID', 'Attrition'])
    y = df['Attrition']
    
    # One-hot encoding
    X_encoded = pd.get_dummies(X, columns=['Department', 'Role'], dtype=int)
    feature_columns = X_encoded.columns.tolist()
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
    
    # Initialize and train the XGBoost model
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
    model.fit(X_train, y_train)
    
    # Evaluation
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print("\n--- Model Evaluation Metrics ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print("--------------------------------\n")
    
    # Save the model and expected features
    print(f"Saving model to {model_path}...")
    joblib.dump({
        'model': model,
        'features': feature_columns
    }, model_path)
    print("Training pipeline completed successfully.")

if __name__ == '__main__':
    main()
