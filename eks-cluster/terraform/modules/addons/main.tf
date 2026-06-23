# ── ArgoCD ───────────────────────────────────────────────
resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "7.3.11"
  namespace        = "argocd"
  create_namespace = true
 
  set {
    name  = "server.service.type"
    value = "LoadBalancer"
  }
 
  timeout = 600
}
 
# ── kube-prometheus-stack ────────────────────────────────
resource "helm_release" "prometheus" {
  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "61.3.2"
  namespace        = "monitoring"
  create_namespace = true
 
  set {
    name  = "grafana.adminPassword"
    value = "admin123"
  }
 
  set {
    name  = "prometheus.prometheusSpec.retention"
    value = "7d"
  }
 
  timeout = 600
}
 
# ── Loki ─────────────────────────────────────────────────
resource "helm_release" "loki" {
  name             = "loki"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "loki"
  version          = "6.6.4"
  namespace        = "monitoring"
  create_namespace = true
 
  values = [<<-YAML
    loki:
      commonConfig:
        replication_factor: 1
      storage:
        type: filesystem
    singleBinary:
      replicas: 1
    monitoring:
      selfMonitoring:
        enabled: false
      lokiCanary:
        enabled: false
    test:
      enabled: false
  YAML
  ]
 
  timeout = 600
}
