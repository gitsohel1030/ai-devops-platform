# AI in DevOps — Learning & Portfolio Platform
 
A hands-on, 12-week project extending a DevOps/Kubernetes background into AI and
MLOps. Each week is a working piece, built on a real AWS account with real
constraints (budget, version conflicts, OS quirks), and documented honestly,
including what broke and how it was fixed.
 
**Status: Weeks 1-5 complete.** An ML model is trained, tracked, containerised,
built and pushed by a CI pipeline, and deployed to EKS by ArgoCD from Git.
 
## Highlights
 
- AI log analyzer: Kubernetes pod logs in, structured incident report out
  (AWS Bedrock, Claude 3 Haiku)
- MLflow tracking server (Docker, S3 artifacts) with a versioned model registry
- FastAPI inference service, containerised and pushed to Amazon ECR
- EKS cluster as Terraform modules: VPC, managed nodes, OIDC, ArgoCD,
  kube-prometheus-stack, Loki
- CI pipeline with an accuracy gate and keyless AWS auth (GitHub OIDC)
- GitOps deployment: ArgoCD syncs the model service from Git (Synced and Healthy)
 
## Repositories
 
| Repo | Contents |
|------|----------|
| `ai-devops-platform` (this repo) | Weeks 1-3: Bedrock analyzer, MLflow, model serving, EKS Terraform |
| `AI-gitops-pipeline` | Weeks 4-5: CI/CD pipeline, Kubernetes manifests, ArgoCD Application |
 
## Environment
 
All work is done over VS Code Remote SSH into a dedicated EC2 workstation, so
nothing needs installing on the local machine.
 
| Item | Value |
|------|-------|
| Cloud | AWS, ap-south-1 (Mumbai) |
| Workstation OS | Ubuntu 26.04 (system Python 3.14) |
| Python for ML work | 3.10.14 via pyenv (see lessons below) |
| Cost control | EKS created per working session, destroyed afterwards, then checked for leftover billable resources |
 
## Repository Structure
 
```
ai-devops-platform/
├── bedrock/          # Week 1: AI log analyzer (AWS Bedrock)
├── mlflow/           # Week 2: MLflow server (Docker Compose) + training script
├── model-serving/    # Week 3: FastAPI inference service, Dockerfile, k8s manifests
├── eks-cluster/      # Week 3 and 5: Terraform for the EKS platform
│   └── terraform/
│       ├── main.tf, variables.tf, outputs.tf, providers.tf
│       └── modules/
│           ├── vpc/      # VPC, public/private subnets, NAT gateway
│           ├── eks/      # cluster, managed node group, OIDC provider
│           └── addons/   # Helm: ArgoCD, kube-prometheus-stack, Loki
├── incident-bot/     # Week 8 (upcoming)
└── README.md
```
 
## How the Pieces Connect
 
```
Week 1   Bedrock log analyzer        AI explains pod failures from raw logs
Week 2   MLflow + model training     experiments tracked, best model versioned
Week 3   FastAPI service -> ECR      model served as a container image
         EKS Terraform               cluster, ArgoCD, Prometheus, Loki
Week 4   CI pipeline                 train -> accuracy gate -> build -> push -> update manifest
Week 5   ArgoCD                      deploys the new image tag from Git to EKS
```
 
End-to-end flow once everything is running:
 
```
git push
   |
   v
GitHub Actions (AI-gitops-pipeline)
   train -> accuracy gate (>= 0.90) -> build image -> push to ECR (SHA tag)
   -> bot commits new tag to k8s/deployment.yaml
   |
   v
ArgoCD on EKS polls Git, syncs namespace ml-models
   |
   v
delay-predictor (2 pods) serving /predict
   (same cluster also runs Prometheus, Grafana and Loki in namespace monitoring)
```
 
## Week 1 — AI Log Analyzer (`bedrock/`)
 
Sends a Kubernetes pod log to Claude 3 Haiku on AWS Bedrock and returns a
structured incident report: severity, root cause, immediate fix, prevention
steps and related components. The report is also saved to a file as an audit trail.
 
- Tested on two failure types: PostgreSQL connection refused, and OOMKilled
  during a bulk image-resize job. Each produced a different, relevant diagnosis.
- Model ID used: `anthropic.claude-3-haiku-20240307-v1:0`
 
## Week 2 — MLflow Tracking Server (`mlflow/`)
 
MLflow 2.19.0 runs in Docker Compose with SQLite for run metadata (persisted in
a named volume) and an S3 bucket for model artifacts. A RandomForest model that
predicts food-delivery delays was trained in four configurations and registered
as `foodrush-delay-predictor`.
 
| Version | Trees | Max depth | Accuracy | F1 | |
|---------|-------|-----------|----------|----|----|
| v1 | 50 | 5 | 90.0% | 0.8750 | |
| v2 | 100 | 10 | 94.0% | 0.9268 | selected |
| v3 | 200 | 15 | 94.0% | 0.9277 | |
| v4 | 100 | none | 93.5% | 0.9217 | |
 
v2 was chosen because deeper or larger models did not improve results
meaningfully, and the simpler model is cheaper to serve.
 
## Week 3 — Model Serving and EKS Platform (`model-serving/`, `eks-cluster/`)
 
**Inference service.** A FastAPI app exposes `/predict`, `/health`, `/ready` and
`/model-info`. Requests are validated with Pydantic, the model is loaded once at
startup (not per request), and the container runs as a non-root user with
liveness and readiness probes in the Kubernetes manifests. The image is pushed to
the ECR repository `foodrush-delay-predictor`.
 
Example request (tested locally and in Docker):
 
```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"distance_km": 12.5, "items_count": 6, "order_hour": 20,
       "weather_condition": 2, "restaurant_rating": 3.2, "day_of_week": 5}'
# {"prediction":1,"label":"DELAYED","confidence":1.0, ...}   (about 6 ms)
```
 
**Cluster.** `eks-cluster/terraform` builds a VPC (public and private subnets,
NAT gateway), an EKS 1.32 cluster with a managed node group of two t3.medium
nodes in private subnets, and an OIDC provider. A Helm-based `addons` module
installs ArgoCD, kube-prometheus-stack and Loki. Loki's settings live in
`modules/addons/loki-values.yaml`.
 
## Weeks 4 and 5 — CI/CD and GitOps (`AI-gitops-pipeline` repo)
 
- A GitHub Actions workflow trains the model, fails the build if accuracy is
  below 0.90, builds the image, pushes it to ECR tagged with the commit SHA, and
  commits the new tag into the Kubernetes manifest.
- AWS access uses GitHub OIDC, so there are no stored access keys.
- An ArgoCD Application watches the `k8s/` folder and deploys it to the
  `ml-models` namespace with automated sync (prune and self-heal).
 
See that repository's README for the pipeline details.
 
## Selected Problems Solved
 
| Week | Problem | Resolution |
|------|---------|------------|
| 1 | Bedrock calls failed: retired model-access page, inference-profile IDs, one-time Anthropic use-case form | Submitted the form and used the on-demand model ID |
| 2 | MLflow 3.x UI blocked its own API calls; 3.x client and 2.x server are not compatible | Pinned server and client to 2.19.0 |
| 2 | `pyarrow` failed to build on Ubuntu 26.04's Python 3.14 (no prebuilt wheels) | Installed Python 3.10.14 with pyenv for all ML work |
| 3 | Container would not start: non-root user could not read packages installed with `pip --user` | Single-stage build with a system-wide install |
| 3 | Loki Helm release timed out: missing `schemaConfig` and `deploymentMode`, cache pods too large for the nodes, read-only `/var/loki` | Dedicated values file (schema, SingleBinary, caches off, writable volume at `/var/loki`); validated with `helm template` before applying |
| 4 | OIDC role assumption denied even with the right role | GitHub's `sub` claim embeds numeric owner and repo IDs; pinned them in the trust policy |
| 5 | Pods in `ErrImagePull` | ECR had no image for the manifest's tag; rebuilt via the pipeline and refreshed ArgoCD |
 
## Known Limitations
 
- Training data is synthetic, so accuracy shows the pipeline works, not
  real-world model quality.
- The EBS CSI driver is not installed, so Loki uses temporary storage, and no log
  shipper is configured yet.
- The MLflow server runs on a single EC2 with SQLite and static AWS credentials;
  production would use a managed database and IAM roles.
- The model service has no metrics, dashboards or alerts yet (Week 6).
 
## Roadmap
 
| Week | Topic | Status |
|------|-------|--------|
| 1 | AWS Bedrock log analyzer | Done |
| 2 | MLflow tracking server and model registry | Done |
| 3 | Model serving, ECR, EKS Terraform | Done |
| 4 | CI pipeline with accuracy gate | Done |
| 5 | ArgoCD GitOps deployment | Done |
| 6 | Model monitoring: Prometheus and Grafana | Next |
| 7 | AWS SageMaker and Bedrock deep dive | Upcoming |
| 8 | AI incident summarizer bot (Slack, Loki, Bedrock) | Upcoming |
| 9 | Anomaly detection on Prometheus metrics | Upcoming |
| 10 | LangChain ops agent | Upcoming |
| 11 | Portfolio documentation | Upcoming |
| 12 | Interview preparation | Upcoming |
