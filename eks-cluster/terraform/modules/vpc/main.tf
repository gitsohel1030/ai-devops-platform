# ── Data Sources ────────────────────────────────────────
# Get available AZs in the region dynamically
# This avoids hardcoding ap-south-1a, ap-south-1b
data "aws_availability_zones" "available" {
  state = "available"
}
 
# ── VPC ─────────────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true   # required for EKS
  enable_dns_support   = true   # required for EKS
 
  tags = {
    Name = "${var.cluster_name}-vpc"
    # These tags are REQUIRED — EKS uses them to discover the VPC
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}
 
# ── Internet Gateway ─────────────────────────────────────
# Allows public subnets to reach the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
 
  tags = {
    Name = "${var.cluster_name}-igw"
  }
}
 
# ── Public Subnets ───────────────────────────────────────
# Used for: Load balancers, NAT gateway
# NOT for worker nodes (security best practice)
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)
 
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
 
  tags = {
    Name = "${var.cluster_name}-public-${count.index + 1}"
    # Required tag — tells EKS this subnet can host public load balancers
    "kubernetes.io/role/elb"                            = "1"
    "kubernetes.io/cluster/${var.cluster_name}"         = "shared"
  }
}
 
# ── Private Subnets ──────────────────────────────────────
# Used for: EKS worker nodes, pods, model serving
# No direct internet access — traffic routes via NAT gateway
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)
 
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
 
  tags = {
    Name = "${var.cluster_name}-private-${count.index + 1}"
    # Required tag — tells EKS this subnet can host internal load balancers
    "kubernetes.io/role/internal-elb"                   = "1"
    "kubernetes.io/cluster/${var.cluster_name}"         = "shared"
  }
}
 
# ── NAT Gateway ──────────────────────────────────────────
# Allows private subnet nodes to reach internet (for pulling images etc.)
# Must live in a PUBLIC subnet
resource "aws_eip" "nat" {
  domain = "vpc"
 
  tags = {
    Name = "${var.cluster_name}-nat-eip"
  }
}
 
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id   # place NAT in first public subnet
 
  tags = {
    Name = "${var.cluster_name}-nat"
  }
 
  depends_on = [aws_internet_gateway.main]
}
 
# ── Route Tables ─────────────────────────────────────────
# Public route table: traffic goes via Internet Gateway
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
 
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
 
  tags = {
    Name = "${var.cluster_name}-public-rt"
  }
}
 
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
 
# Private route table: traffic goes via NAT Gateway
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
 
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
 
  tags = {
    Name = "${var.cluster_name}-private-rt"
  }
}
 
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
