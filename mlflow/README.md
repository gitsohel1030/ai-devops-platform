# Week 2 — MLflow Tracking Server
 
## What is MLflow and Why It Matters
 
MLflow is the industry-standard open-source platform for managing the ML lifecycle.
Every company doing ML — Google, Netflix, Uber, and enterprise MNCs — uses MLflow
or an equivalent tool. As an MLOps engineer, you don't train models — you build and
operate the platform that data scientists use to track, version, and deploy them.
 
MLflow does 4 things:
- TRACKING  → logs every experiment automatically (params, metrics, artifacts)
- REGISTRY  → versions models through Staging → Production → Archived
- PROJECTS  → packages code for reproducibility
- MODELS    → standardized format to deploy anywhere (Flask, EKS, SageMaker)
 
## Architecture
 
```
Your Laptop (VS Code SSH)
        │
        ▼
EC2 t3.large (ai-workstation) — Ubuntu 26.04
        │
        ├── MLflow Server (Docker container — port 5000)
        │       ├── Backend Store → SQLite (experiment metadata)
        │       │   stored in Docker named volume (survives restarts)
        │       └── Artifact Store → S3
        │           s3://mlflow-artifacts-608827180555/artifacts
        │           (model files, CSVs, plots — permanent storage)
        │
        └── Python 3.10.14 (via pyenv)
                └── train-model.py
                        └── mlflow client → sends data to MLflow server
```
 
## Tech Stack
 
| Component      | Technology                      | Version  |
|----------------|---------------------------------|----------|
| MLflow Server  | Docker (ghcr.io/mlflow/mlflow)  | 2.19.0   |
| Backend Store  | SQLite                          | built-in |
| Artifact Store | AWS S3                          | —        |
| ML Framework   | scikit-learn RandomForest       | latest   |
| Python         | pyenv managed                   | 3.10.14  |
| Orchestration  | Docker Compose                  | v2       |
 
## Project Structure
 
```
week2-mlflow/
├── docker-compose.yaml   # MLflow server definition
├── train-model.py        # FoodRush delay predictor + MLflow tracking
├── requirements.txt      # Pinned Python dependencies
├── .env                  # AWS credentials (gitignored)
├── .gitignore
└── README.md
```
 
## Setup and Usage
 
### Prerequisites
- Docker installed and running
- AWS credentials configured (~/.aws/credentials)
- Python 3.10.14 via pyenv
- S3 bucket: mlflow-artifacts-608827180555
 
### Start MLflow Server
```bash
docker compose up -d
docker compose ps
docker compose logs mlflow --tail=20
```
 
### Access MLflow UI
```
http://<EC2_PUBLIC_IP>:5000
```
 
### Create Python Environment
```bash
# Must use Python 3.10 — mlflow 2.x incompatible with Python 3.14
~/.pyenv/versions/3.10.14/bin/python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
 
### Run Experiments
```bash
source venv/bin/activate
python3 train-model.py
```
 
### Stop Server
```bash
docker compose down      # stops container, keeps volume + data
docker compose down -v   # stops container AND deletes all data
```
 
## Experiment Results — FoodRush Order Delay Predictor
 
### Problem Statement
Predict whether a FoodRush delivery order will be delayed based on:
- Distance from restaurant to customer
- Number of items in order
- Order hour (peak vs off-peak)
- Weather condition
- Restaurant rating
- Day of week
 
### Model: RandomForest Classifier
 
| Version | n_estimators | max_depth | Accuracy | Precision | Recall | F1     |        |
|---------|-------------|-----------|----------|-----------|--------|--------|--------|
| v1      | 50          | 5         | 90.0%    | 0.8974    | 0.8537 | 0.8750 |        |
| v2      | 100         | 10        | 94.0%    | 0.9268    | 0.9268 | 0.9268 | ✅ BEST |
| v3      | 200         | 15        | 94.0%    | 0.9167    | 0.9390 | 0.9277 |        |
| v4      | 100         | None      | 93.5%    | 0.9107    | 0.9329 | 0.9217 |        |
 
### Winner: v2 — 100 trees, depth 10
- Best balance of accuracy and complexity
- Lower complexity than v3 with identical accuracy
- Registered in MLflow Model Registry as foodrush-delay-predictor
- Model artifacts stored in S3 automatically
 
## MLflow Workflow (Real World Pattern)
 
```
Data Scientist trains experiments
        ↓
MLflow Tracking logs everything automatically
        ↓
Team reviews UI — picks best run
        ↓
Best model promoted to Registry → Staging
        ↓
MLOps Engineer (you) deploys Staging → runs tests
        ↓
Passes tests → promoted to Production
        ↓
CI/CD pipeline detects new Production model
        ↓
Deploys to EKS via ArgoCD (Week 3)
```
 
## Key Lessons Learned
 
### Version Compatibility is Critical
MLflow 3.x client cannot talk to MLflow 2.x server — API endpoints differ.
Always pin versions in requirements.txt. Never use pip install mlflow without
a version pin in production.
 
### Python Version Matters for ML
Python 3.14 (Ubuntu 26.04 default) is too new — no pre-built wheels for ML
libraries yet. pip falls back to compiling from source which fails without
cmake and other build tools. Solution: pyenv to manage Python versions
independently of the OS.
 
### Docker Named Volumes vs Bind Mounts
Named volume (mlflow-db) persists SQLite database across container restarts.
docker compose down keeps the volume. docker compose down -v deletes it.
Always use named volumes for stateful services in production.
 
### AWS Credentials in Docker
Never hardcode credentials in docker-compose.yaml — it ends up in git.
Use .env file (gitignored) to pass credentials as environment variables.
In production: use IAM Instance Roles instead of access keys entirely.
 
## Issues Encountered and Fixed
 
| Issue                          | Root Cause                        | Fix                             |
|--------------------------------|-----------------------------------|---------------------------------|
| restarts not allowed           | Typo + wrong indentation          | restart at service level        |
| Invalid host header            | MLflow 3.x security               | Downgraded to 2.19.0            |
| --host-allowlist not found     | Flag renamed in 3.x               | Used --allowed-hosts            |
| 403 on all API calls           | MLflow 3.x cross-origin blocking  | Downgraded to stable 2.19.0     |
| alembic revision not found     | DB created by 3.x, read by 2.x   | docker compose down -v          |
| pyarrow compile failure        | Python 3.14 no pre-built wheels   | pyenv Python 3.10.14            |
| NoCredentialsError in Docker   | Container has no ~/.aws access    | Mount -v ~/.aws:/root/.aws      |
| python3.10 not found in apt    | Ubuntu 26.04 too new for PPA      | pyenv from source               |
 
## AWS Resources Created
 
| Resource    | Name                            | Purpose                  |
|-------------|---------------------------------|--------------------------|
| S3 Bucket   | mlflow-artifacts-608827180555   | Model artifact storage   |
| IAM Policy  | MLflowS3Access                  | Least-privilege S3 access|
| Docker Volume | week2-mlflow_mlflow-db        | SQLite persistence       |
 
## Cost
 
| Resource      | Usage                          | Cost          |
|---------------|--------------------------------|---------------|
| EC2 t3.large  | ~3 hrs/day, stopped otherwise  | ~$7/month     |
| S3 storage    | Small models ~50MB total       | <$0.01/month  |
| S3 requests   | Training runs only             | <$0.01 total  |
 
## Next Step — Week 3
 
Containerize the best model (v2, foodrush-delay-predictor) as a FastAPI
inference API, push Docker image to ECR, and deploy to EKS via ArgoCD.
This turns the trained model into a live production ML service.
