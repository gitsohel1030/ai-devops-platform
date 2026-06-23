"""
Model loading and inference logic.
 
Separated from main.py intentionally — clean separation of concerns.
In production you would load from MLflow model registry using:
  mlflow.sklearn.load_model("models:/foodrush-delay-predictor/Production")
 
For portability (no MLflow dependency at inference time), we load
the model artifact directly from S3 using joblib.
This is the pattern used by companies that want lightweight inference
containers without the full MLflow stack as a dependency.
"""
 
import os
import boto3
import joblib
import logging
import numpy as np
import tempfile
 
logger = logging.getLogger(__name__)
 
# Global model object — loaded once at startup, reused for every request
_model = None
model_loaded = False
 
 
def load_model():
    """
    Load model from S3 artifact store.
 
    Why S3 directly instead of MLflow API?
    - Inference container stays lightweight (no mlflow dependency)
    - Works even if MLflow server is down
    - Faster cold start — direct S3 download vs MLflow REST API call
    - Production pattern at Netflix, Uber, and most large ML platforms
 
    Model path in S3:
    s3://mlflow-artifacts-608827180555/artifacts/<experiment_id>/<run_id>/
    artifacts/random-forest-model/model.pkl
    """
    global _model, model_loaded
 
    # Get config from environment variables
    # These are injected by Kubernetes via the Deployment manifest
    s3_bucket  = os.getenv("MODEL_S3_BUCKET", "mlflow-artifacts-608827180555")
    model_path = os.getenv("MODEL_S3_KEY", "")
 
    if not model_path:
        # Fallback: train a fresh model if no S3 path provided
        # Useful for local development and testing
        logger.warning("MODEL_S3_KEY not set — training fresh model for dev/test")
        _model = _train_fallback_model()
        model_loaded = True
        return
 
    try:
        logger.info(f"Downloading model from s3://{s3_bucket}/{model_path}")
 
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))
 
        # Download to temp file — joblib needs a file path not bytes
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
            s3.download_fileobj(s3_bucket, model_path, tmp)
            tmp_path = tmp.name
 
        _model = joblib.load(tmp_path)
        os.unlink(tmp_path)  # clean up temp file
 
        model_loaded = True
        logger.info("Model loaded from S3 successfully")
 
    except Exception as e:
        logger.error(f"Failed to load model from S3: {e}")
        logger.warning("Falling back to freshly trained model")
        _model = _train_fallback_model()
        model_loaded = True
 
 
def predict(features: list) -> tuple[int, float]:
    """
    Run inference on a single order.
 
    Args:
        features: [distance_km, items_count, order_hour,
                   weather_condition, restaurant_rating, day_of_week]
 
    Returns:
        (prediction, confidence) where prediction is 0 or 1
    """
    if _model is None:
        raise RuntimeError("Model not loaded")
 
    # Reshape to 2D array — sklearn expects (n_samples, n_features)
    X = np.array(features).reshape(1, -1)
 
    prediction = int(_model.predict(X)[0])
 
    # predict_proba returns [[prob_class0, prob_class1]]
    # We return the probability of the predicted class
    probabilities = _model.predict_proba(X)[0]
    confidence = float(probabilities[prediction])
 
    return prediction, confidence
 
 
def _train_fallback_model():
    """
    Train a fresh model for local dev/testing when S3 is unavailable.
    Uses same data generation logic as Week 2 train-model.py.
    """
    from sklearn.ensemble import RandomForestClassifier
    import pandas as pd
 
    logger.info("Training fallback model...")
    np.random.seed(42)
    n = 2000
 
    distance     = np.random.uniform(0.5, 15.0, n)
    items        = np.random.randint(1, 10, n)
    hour         = np.random.randint(0, 24, n)
    weather      = np.random.choice([0, 1, 2], n, p=[0.6, 0.3, 0.1])
    rating       = np.random.uniform(2.0, 5.0, n)
    day          = np.random.randint(0, 7, n)
 
    X = np.column_stack([distance, items, hour, weather, rating, day])
 
    delay_prob = (
        (distance / 15.0) * 0.3 +
        (weather  /  2.0) * 0.3 +
        (((hour >= 12) & (hour <= 14)) | ((hour >= 19) & (hour <= 21))).astype(int) * 0.2 +
        (items / 10.0) * 0.1 +
        np.random.uniform(0, 0.1, n)
    )
    y = (delay_prob > 0.4).astype(int)
 
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
 
    logger.info("Fallback model trained successfully")
    return model
