module "vpc" {
  source = "./modules/vpc"
 
  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}
 
module "eks" {
  source = "./modules/eks"
 
  cluster_name        = var.cluster_name
  cluster_version     = var.cluster_version
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_type  = var.node_instance_type
  node_desired_count  = var.node_desired_count
  node_min_count      = var.node_min_count
  node_max_count      = var.node_max_count
}
 
module "addons" {
  source = "./modules/addons"
 
  cluster_name = var.cluster_name
 
  depends_on = [module.eks]
}
