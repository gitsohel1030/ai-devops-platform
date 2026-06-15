"""
FoodRush Order Delay Predictor
Week 2 - MLflow Experiment Tracking
 
Real-world scenario: Predict whether a food delivery order will be delayed
based on order characteristics. This is exactly the kind of model a company
like Swiggy or Zomato would build and track with MLflow.
 
Author: Sohel Mubarak Mujawar
"""
 
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
import argparse
import os
 
 
def generate_foodrush_data(n_samples=1000):
    """
    Generate realistic FoodRush order data.
 
    In production this would come from your PostgreSQL database:
    SELECT order_time, restaurant_distance, items_count,
           weather_condition, was_delayed
    FROM orders WHERE created_at > NOW() - INTERVAL '30 days'
    """
    np.random.seed(42)
 
    data = {
        # Distance from restaurant to customer (km)
        'distance_km': np.random.uniform(0.5, 15.0, n_samples),
 
        # Number of items in order
        'items_count': np.random.randint(1, 10, n_samples),
 
        # Hour of day order was placed (0-23)
        'order_hour': np.random.randint(0, 24, n_samples),
 
        # Weather: 0=clear, 1=rainy, 2=heavy_rain
        'weather_condition': np.random.choice([0, 1, 2], n_samples,
                                               p=[0.6, 0.3, 0.1]),
 
        # Restaurant rating (1-5)
        'restaurant_rating': np.random.uniform(2.0, 5.0, n_samples),
 
        # Day of week (0=Monday, 6=Sunday)
        'day_of_week': np.random.randint(0, 7, n_samples),
    }
 
    df = pd.DataFrame(data)
 
    # Create realistic delay logic:
    # High distance + bad weather + peak hours = more likely delayed
    delay_probability = (
        (df['distance_km'] / 15.0) * 0.3 +        # Distance factor
        (df['weather_condition'] / 2.0) * 0.3 +    # Weather factor
        ((df['order_hour'].between(12, 14) |
          df['order_hour'].between(19, 21)).astype(int)) * 0.2 +  # Peak hours
        (df['items_count'] / 10.0) * 0.1 +         # Large order factor
        np.random.uniform(0, 0.1, n_samples)        # Random noise
    )
 
    df['was_delayed'] = (delay_probability > 0.4).astype(int)
 
    return df
 
 
def train_and_track(n_estimators, max_depth, experiment_name):
    """
    Train model and log everything to MLflow.
 
    This function is called multiple times with different parameters
    to compare experiments — that's the core MLflow use case.
    """
 
    # Point MLflow to your tracking server on EC2
    # In production this would be an internal DNS name like:
    # http://mlflow.internal.company.com:5000
    mlflow.set_tracking_uri("http://localhost:5000")
 
    # Create or get experiment — like a folder grouping related runs
    mlflow.set_experiment(experiment_name)
 
    # Generate data
    print(f"\nTraining with: n_estimators={n_estimators}, max_depth={max_depth}")
    df = generate_foodrush_data(n_samples=2000)
 
    features = ['distance_km', 'items_count', 'order_hour',
                'weather_condition', 'restaurant_rating', 'day_of_week']
    X = df[features]
    y = df['was_delayed']
 
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
 
    # ── MLflow run starts here ──────────────────────────────────
    with mlflow.start_run():
 
        # 1. Log parameters — what settings you used
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("features", features)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
 
        # 2. Train the model
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
 
        # 3. Evaluate
        y_pred = model.predict(X_test)
        accuracy  = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall    = recall_score(y_test, y_pred)
        f1        = f1_score(y_test, y_pred)
 
        # 4. Log metrics — what results you got
        mlflow.log_metric("accuracy",  accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall",    recall)
        mlflow.log_metric("f1_score",  f1)
 
        # 5. Log the model itself — saves to S3 automatically
        mlflow.sklearn.log_model(
            model,
            "random-forest-model",
            registered_model_name="foodrush-delay-predictor"
        )
 
        # 6. Log feature importance as a custom artifact
        importance_df = pd.DataFrame({
            'feature': features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
 
        importance_df.to_csv("feature_importance.csv", index=False)
        mlflow.log_artifact("feature_importance.csv")
 
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        print(f"  Model logged to S3 via MLflow ✅")
 
    # ── MLflow run ends here ────────────────────────────────────
 
 
def main():
    experiment_name = "foodrush-delay-prediction"
 
    print("="*55)
    print("  FoodRush Delay Predictor — MLflow Tracking Demo")
    print("="*55)
    print(f"  MLflow UI: http://localhost:5000")
    print(f"  Experiment: {experiment_name}")
    print("  Running 4 experiments with different parameters...")
 
    # Run multiple experiments — this is what MLflow is FOR
    # Compare results in the UI at http://<EC2_IP>:5000
    experiments = [
        {"n_estimators": 50,  "max_depth": 5},
        {"n_estimators": 100, "max_depth": 10},
        {"n_estimators": 200, "max_depth": 15},
        {"n_estimators": 100, "max_depth": None},   # None = unlimited depth
    ]
 
    for params in experiments:
        train_and_track(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            experiment_name=experiment_name
        )
 
    print("\n" + "="*55)
    print("  All 4 experiments complete!")
    print(f"  Open http://65.1.167.189:5000 to compare results")
    print("  Check S3 for saved model artifacts:")
    print("  aws s3 ls s3://mlflow-artifacts-608827180555/ --recursive")
    print("="*55)
 
 
if __name__ == "__main__":
    main()
