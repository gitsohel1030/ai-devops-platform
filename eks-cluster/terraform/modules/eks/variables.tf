variable "cluster_name"        { type = string }
variable "cluster_version"     { type = string }
variable "public_subnet_ids"   { type = list(string) }
variable "private_subnet_ids"  { type = list(string) }
variable "node_instance_type"  { type = string }
variable "node_desired_count"  { type = number }
variable "node_min_count"      { type = number }
variable "node_max_count"      { type = number }
