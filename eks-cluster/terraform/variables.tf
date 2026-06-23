
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}
 
variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "ai-platform-cluster"
}
 
variable "cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.32"
}
 
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}
 
variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}
 
variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}
 
variable "node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "c7i-flex.large"
}
 
variable "node_desired_count" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}
 
variable "node_min_count" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}
 
variable "node_max_count" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 3
}
 

 