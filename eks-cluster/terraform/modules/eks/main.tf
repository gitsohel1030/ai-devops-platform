# ── IAM Role for EKS Control Plane ──────────────────────
# EKS cluster itself needs permissions to manage AWS resources
resource "aws_iam_role" "cluster" {
  name = "${var.cluster_name}-cluster-role"
 
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}
 
resource "aws_iam_role_policy_attachment" "cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}
 
# ── EKS Cluster ──────────────────────────────────────────
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.cluster_version
  role_arn = aws_iam_role.cluster.arn
 
  vpc_config {
    subnet_ids              = concat(var.public_subnet_ids, var.private_subnet_ids)
    endpoint_private_access = true
    endpoint_public_access  = true   # allows kubectl from your EC2
  }
 
  depends_on = [aws_iam_role_policy_attachment.cluster_policy]
 
  tags = {
    Name = var.cluster_name
  }
}
 
# ── OIDC Provider ────────────────────────────────────────
# Required for IRSA (IAM Roles for Service Accounts)
# Allows pods to assume IAM roles without hardcoded credentials
data "tls_certificate" "cluster" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}
 
resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}
 
# ── IAM Role for Worker Nodes ────────────────────────────
resource "aws_iam_role" "nodes" {
  name = "${var.cluster_name}-node-role"
 
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}
 
resource "aws_iam_role_policy_attachment" "node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"   # for model artifacts
  ])
 
  policy_arn = each.value
  role       = aws_iam_role.nodes.name
}
 
# ── Managed Node Group ───────────────────────────────────
# AWS manages node lifecycle — patching, replacement, scaling
# Nodes go in PRIVATE subnets (security best practice)
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.nodes.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = [var.node_instance_type]
 
  scaling_config {
    desired_size = var.node_desired_count
    min_size     = var.node_min_count
    max_size     = var.node_max_count
  }
 
  update_config {
    max_unavailable = 1   # only 1 node down at a time during updates
  }
 
  depends_on = [aws_iam_role_policy_attachment.node_policies]
 
  tags = {
    Name = "${var.cluster_name}-nodes"
  }
}
