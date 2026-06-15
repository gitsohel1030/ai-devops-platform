# AI in DevOps — Learning & Portfolio Platform
⁠
This repository documents a hands-on, 12-week journey extending a production-grade
DevOps/Kubernetes background into AI/MLOps. Each week is a self-contained project
with its own README, code, and lessons learned — built on a real AWS account with
real constraints (budget, version conflicts, OS quirks) and documented honestly,
including what broke and how it was fixed.
⁠
## Author Context
⁠
DevOps & Infrastructure Automation Engineer (3+ years), working on Ansible
automation, CI/CD pipelines, and Kubernetes operations professionally. This
repo is the personal upskilling track toward MLOps / AI Platform Engineer roles,
built on top of an existing production EKS platform (FoodRush — separate repos).
⁠
## Environment
⁠
All work is done via VS Code Remote SSH into a dedicated EC2 instance —
no local installs required (useful when working from a locked-down org laptop).
⁠
| Item             | Value                          |
|------------------|--------------------------------|
| Cloud            | AWS (ap-south-1 / Mumbai)       |
| Workstation      | EC2 t3.large, Ubuntu 26.04      |
| Access           | VS Code Remote SSH              |
| Python (system)  | 3.14 (OS default)                |
| Python (ML work) | 3.10.14 via pyenv (required)    |
| Cost discipline  | Stop EC2 when idle, S3 for artifacts |
⁠
## Repository Structure
⁠
```
ai-devops-platform/
├── week1-bedrock/
│   ├── log-analyzer.py
│   ├── sample-pod-log.txt
│   ├── oom-log.txt
│   └── README.md
├── week2-mlflow/
│   ├── docker-compose.yaml
│   ├── train-model.py
│   ├── requirements.txt
│   └── README.md
├── week3-model-serving/      (upcoming)
├── week8-incident-bot/       (upcoming)
└── README.md   ← this file
```
⁠
## Week 1 — AI-Powered Kubernetes Log Analyzer (AWS Bedrock)
⁠
**Goal:** Use a foundation model to automatically diagnose Kubernetes pod
failures from raw logs — the #1 real-world use case for AI in SRE/DevOps.
⁠
**What it does:**
- Takes any pod log (file, kubectl output, or Loki query result)
- Sends it to Claude 3 Haiku via AWS Bedrock (ap-south-1)
- Returns a structured incident report: severity, root cause, immediate fix,
  prevention steps, related components to check
- Saves the report to disk for audit trail
⁠
**Tech stack:** Python, boto3, AWS Bedrock (anthropic.claude-3-haiku-20240307-v1:0)
⁠
**Tested scenarios:**
- PostgreSQL connection refused (CRITICAL) → correctly diagnosed DB unreachable,
  recommended connection pooling + exponential backoff
- OOMKilled during bulk image processing (CRITICAL) → correctly diagnosed memory
  limit exceeded, recommended limit increase + processing optimization
⁠
**Key lessons:**
- AWS Bedrock's old "Model access" console page is retired — models are now
  auto-available; Anthropic models need a one-time use case form submission
- Correct model ID format: `anthropic.claude-3-haiku-20240307-v1:0`
  (not the `apac.` / `global.` inference profile IDs, which need a different API)
- Response parsing: `json.loads(response['body'].read())`, not `json.load()`
⁠
Full details: [`week1-bedrock/README.md`](./week1-bedrock/README.md)
⁠
## Week 2 — MLflow Tracking Server (Experiment Tracking + Model Registry)
⁠
**Goal:** Stand up the industry-standard ML experiment tracking platform and
use it to train, compare, and version a real model.
⁠
**What it does:**
- MLflow 2.19.0 server running in Docker on the EC2 workstation
- SQLite backend store (experiment metadata) in a persistent Docker volume
- S3 artifact store (`s3://mlflow-artifacts-608827180555`) for model files
- A RandomForest model (`foodrush-delay-predictor`) trained across 4
  hyperparameter configurations, all automatically tracked and versioned
⁠
**Tech stack:** Docker Compose, MLflow 2.19.0, scikit-learn, S3, Python 3.10.14 (pyenv)
⁠
**Results:**
⁠
| Version | Trees | Depth | Accuracy | F1     |        |
|---------|-------|-------|----------|--------|--------|
| v1      | 50    | 5     | 90.0%    | 0.8750 |        |
| v2      | 100   | 10    | 94.0%    | 0.9268 | ✅ BEST |
| v3      | 200   | 15    | 94.0%    | 0.9277 |        |
| v4      | 100   | None  | 93.5%    | 0.9217 |        |
⁠
**Key lessons:**
- MLflow 2.x and 3.x clients/servers are NOT cross-compatible (different REST APIs)
- Ubuntu 26.04 ships Python 3.14, which has no pre-built wheels for many ML
  libraries (pyarrow etc.) — pyenv + Python 3.10.14 is the fix
- MLflow needs AWS credentials inside its container for S3 — pass via `.env`,
  never hardcode in `docker-compose.yaml`
- Docker named volumes preserve SQLite state across `docker compose down`
  (but not `down -v`)
⁠
Full details: [`week2-mlflow/README.md`](./week2-mlflow/README.md)
⁠
## How These Connect (The Bigger Picture)
⁠
```
Week 1: AI reads logs and explains failures
            ↓
Week 2: MLflow tracks and versions ML models
            ↓
Week 3: Best model containerized + deployed to EKS (upcoming)
            ↓
Week 4-7: CI/CD for ML, GitOps deployment, monitoring (upcoming)
            ↓
Week 8: AI incident bot combines Week 1 + Week 2+ skills,
        posts automated RCA to Slack on Alertmanager alerts (upcoming)
```
⁠
The end goal is a single coherent platform: an EKS cluster running real
microservices, observability via Prometheus/Loki, ML models served and
monitored via MLflow + FastAPI, and an AI layer that explains incidents
and anomalies automatically.
⁠
## Running Any Week's Project
⁠
Each week folder is self-contained. General pattern:
⁠
```bash
cd weekN-xxx
⁠
# If Python is involved
~/.pyenv/versions/3.10.14/bin/python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
⁠
# If Docker is involved
docker compose up -d
```
⁠
See each week's README for specifics.
⁠
## Roadmap (12 Weeks)
⁠
| Week | Topic                                          | Status      |
|------|------------------------------------------------|-------------|
| 1    | AWS Bedrock — AI log analyzer                   | ✅ Done     |
| 2    | MLflow tracking server + model registry         | ✅ Done     |
| 3    | Containerize model, push to ECR, deploy to EKS  | Upcoming    |
| 4    | GitHub Actions ML pipeline (train/test/push)    | Upcoming    |
| 5    | ArgoCD GitOps for model deployment              | Upcoming    |
| 6    | Model monitoring — Prometheus + Grafana          | Upcoming    |
| 7    | AWS SageMaker + Bedrock deep dive               | Upcoming    |
| 8    | AI incident summarizer bot (Slack + Loki)        | Upcoming    |
| 9    | Anomaly detection on Prometheus metrics          | Upcoming    |
| 10   | LangChain ops agent (kubectl via Slack)          | Upcoming    |
| 11   | Portfolio documentation sprint                   | Upcoming    |
| 12   | Interview prep + applications                   | Upcoming    |
