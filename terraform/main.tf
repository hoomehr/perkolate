# Terraform Block: Define providers and required versions
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider Configuration
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1" # Choose your region
}

variable "environment" {
  description = "Deployment environment name (e.g., staging, prod)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets (must be in different AZs)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"] # Example for 2 AZs
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets (must be in different AZs)"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"] # Example for 2 AZs
}

variable "availability_zones" {
  description = "List of Availability Zones to use"
  type        = list(string)
  # Data source will populate this dynamically if not specified
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
  # For production, fetch this from a secure source or use random_password
}

variable "db_name" {
  description = "Name for the PostgreSQL database"
  type        = string
  default     = "mydjangodb"
}

variable "app_image_url" {
  description = "URL of the Docker image in ECR (e.g., ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/my-django-app:latest)"
  type        = string
  # Ensure this image exists in ECR before applying
}

variable "app_container_port" {
  description = "Port the application container listens on (e.g., Gunicorn port)"
  type        = number
  default     = 8000
}

variable "app_cpu" {
  description = "Fargate Task CPU units (e.g., 256=0.25vCPU, 512=0.5vCPU, 1024=1vCPU)"
  type        = number
  default     = 512 # 0.5 vCPU
}

variable "app_memory" {
  description = "Fargate Task Memory MiB (e.g., 512=0.5GB, 1024=1GB, 2048=2GB)"
  type        = number
  default     = 1024 # 1 GB
}

variable "app_desired_count" {
  description = "Desired number of application tasks for ECS service"
  type        = number
  default     = 2
}

variable "app_max_capacity" {
  description = "Maximum number of tasks for auto-scaling"
  type        = number
  default     = 6
}

variable "app_min_capacity" {
  description = "Minimum number of tasks for auto-scaling"
  type        = number
  default     = 2
}

variable "domain_name" {
  description = "Your registered domain name (e.g., example.com)"
  type        = string
  # Required for Route 53, ACM, CloudFront CNAME
}

variable "app_subdomain" {
  description = "Subdomain for the application (e.g., www, app)"
  type        = string
  default     = "app"
}

variable "static_bucket_name" {
  description = "Globally unique name for the S3 static assets bucket"
  type        = string
  # Will be generated if left empty
}

# --- Data Sources ---
data "aws_availability_zones" "available" {
  state = "available"
}

# Use specific AZs if needed, otherwise use the data source
locals {
  azs                 = length(var.availability_zones) > 0 ? var.availability_zones : slice(data.aws_availability_zones.available.names, 0, 2) # Use first 2 available AZs by default
  num_azs             = length(local.azs)
  resource_prefix     = "djapp-${var.environment}"
  # Generate unique bucket name if not provided
  s3_bucket_name    = var.static_bucket_name != "" ? var.static_bucket_name : "${local.resource_prefix}-static-assets-${substr(md5(var.vpc_cidr), 0, 8)}"
  app_domain_name     = "${var.app_subdomain}.${var.domain_name}"
  # Combine DB credentials into a single JSON string for Secrets Manager
  db_credentials = jsonencode({
    username = var.db_username
    password = var.db_password
    engine = "postgres" # Django needs this
    host = aws_rds_cluster_instance.main[0].endpoint # Use instance endpoint for Django
    port = aws_db_instance.main[0].port # Use instance port
    dbName = aws_db_instance.main[0].db_name # Use db name from resource
  })
}

# --- Networking (VPC, Subnets, IGW, NAT GW, Routes) ---
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.resource_prefix}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  public_subnets  = slice(var.public_subnet_cidrs, 0, local.num_azs)
  private_subnets = slice(var.private_subnet_cidrs, 0, local.num_azs)

  enable_nat_gateway   = true
  single_nat_gateway   = false # Use one NAT Gateway per AZ for HA
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Terraform   = "true"
    Project     = "DjangoApp"
  }

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1" # Although not K8s, helps identify usage
  }
}

# --- Security Groups ---
resource "aws_security_group" "alb_sg" {
  name        = "${local.resource_prefix}-alb-sg"
  description = "Security group for the Application Load Balancer"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere"
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from anywhere"
  }

  egress {
    protocol    = "-1" # Allow all outbound traffic
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${local.resource_prefix}-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "ecs_tasks_sg" {
  name        = "${local.resource_prefix}-ecs-tasks-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = module.vpc.vpc_id

  # Allow inbound traffic only from the ALB
  ingress {
    protocol        = "tcp"
    from_port       = var.app_container_port
    to_port         = var.app_container_port
    security_groups = [aws_security_group.alb_sg.id]
    description     = "Allow traffic from ALB"
  }

  # Allow all outbound traffic (adjust if stricter control is needed)
  # Needs outbound access for NAT Gateway -> Internet (e.g., external APIs, package installs)
  # Needs outbound access to RDS
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${local.resource_prefix}-ecs-tasks-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "${local.resource_prefix}-rds-sg"
  description = "Security group for RDS PostgreSQL instance"
  vpc_id      = module.vpc.vpc_id

  # Allow inbound traffic only from ECS tasks on the PostgreSQL port
  ingress {
    protocol        = "tcp"
    from_port       = 5432 # Default PostgreSQL port
    to_port         = 5432
    security_groups = [aws_security_group.ecs_tasks_sg.id]
    description     = "Allow PostgreSQL traffic from ECS Tasks"
  }

  # Egress is typically not needed for RDS itself unless it initiates connections outwards

  tags = {
    Name        = "${local.resource_prefix}-rds-sg"
    Environment = var.environment
  }
}

# --- Secrets Manager ---
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${local.resource_prefix}/db/credentials"
  description = "Database credentials for the Django application"
  # KMS key can be specified if needed: kms_key_id = aws_kms_key.secrets.arn
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id     = aws_secretsmanager_secret.db_credentials.id
  secret_string = local.db_credentials # Store JSON string
}

# --- RDS PostgreSQL Database ---
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "${local.resource_prefix}-rds-subnet-group"
  subnet_ids = module.vpc.private_subnets # Deploy RDS in private subnets

  tags = {
    Name = "${local.resource_prefix}-rds-subnet-group"
  }
}

# Note: Consider using aws_rds_cluster for Aurora PostgreSQL for better scaling/availability if budget allows.
# This example uses standard RDS PostgreSQL Multi-AZ.
resource "aws_db_instance" "main" {
  # count                 = 1 # Only create one primary instance (Multi-AZ handles standby)
  identifier            = "${local.resource_prefix}-rds"
  allocated_storage     = 20             # Minimum GB
  engine                = "postgres"
  engine_version        = "15.5"         # Specify desired version
  instance_class        = "db.t3.small" # Choose appropriate instance class
  db_name               = var.db_name
  username              = var.db_username # Will be managed by RDS after initial creation
  password              = var.db_password # Will be managed by RDS after initial creation
  db_subnet_group_name  = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  parameter_group_name  = "default.postgres15" # Or a custom parameter group
  multi_az              = true                 # Enable High Availability
  publicly_accessible   = false
  storage_type          = "gp3"              # General Purpose SSD v3 recommended
  # iops                  = 3000             # Required if storage_type is io1, optional for gp3 to provision higher IOPS
  # storage_throughput    = 125              # Optional for gp3
  backup_retention_period = 7                # Days
  skip_final_snapshot   = false            # Set to true for non-prod quick deletion, false for prod
  deletion_protection   = true             # Recommended for production
  apply_immediately     = false            # Set to true to apply changes immediately (may cause downtime)

  tags = {
    Name        = "${local.resource_prefix}-rds"
    Environment = var.environment
  }

  # If using Secrets Manager for rotation, remove username/password fields above
  # manage_master_user_password = true
  # master_user_secret_kms_key_id = aws_kms_key.secrets.arn # requires KMS key

  # It is generally better to create the user/password initially
  # and then manage rotations OUTSIDE of Terraform if needed, or via RDS managed rotation if supported.
  # Providing them here ensures TF can create the DB. For rotation, use Secrets Manager rotation feature.
}

# --- ECR Repository ---
resource "aws_ecr_repository" "app_repo" {
  name                 = "${local.resource_prefix}-app"
  image_tag_mutability = "MUTABLE" # Or IMMUTABLE for stricter versioning

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${local.resource_prefix}-app-repo"
    Environment = var.environment
  }
}

# --- IAM Roles for ECS ---
data "aws_iam_policy_document" "ecs_task_execution_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name               = "${local.resource_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_role_policy.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  # This policy allows pulling images from ECR and sending logs to CloudWatch
}

# Optional: Add policy to access Secrets Manager if secrets are fetched at container start by Fargate agent
resource "aws_iam_role_policy" "ecs_execution_secrets_policy" {
  name = "${local.resource_prefix}-ecs-execution-secrets-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
          # Needed if using KMS encryption for the secret
          # "kms:Decrypt"
        ]
        Effect   = "Allow"
        Resource = [
          aws_secretsmanager_secret.db_credentials.arn,
          # Add KMS key ARN here if used
        ]
      },
    ]
  })
}


data "aws_iam_policy_document" "ecs_task_role_policy_doc" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "${local.resource_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_role_policy_doc.json
}

# Grant Task Role permissions needed by the application itself
# (e.g., access S3, other AWS services, maybe Secrets Manager if app fetches directly)
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${local.resource_prefix}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Example: Allow reading the secret from within the application code
      # {
      #   Action = [
      #     "secretsmanager:GetSecretValue",
      #     "kms:Decrypt" # If using KMS
      #   ]
      #   Effect   = "Allow"
      #   Resource = [
      #      aws_secretsmanager_secret.db_credentials.arn,
      #      # Add KMS key ARN here if used
      #    ]
      # },
      # Example: Allow application to put objects into the static S3 bucket (if needed)
      # {
      #   Action = ["s3:PutObject", "s3:PutObjectAcl"] # Adjust as needed
      #   Effect   = "Allow"
      #   Resource = ["${aws_s3_bucket.static_assets.arn}/*"]
      # },
      # Add other permissions your application needs here
    ]
  })
}

# --- CloudWatch Log Group ---
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${local.resource_prefix}-app"
  retention_in_days = 30 # Adjust retention as needed

  tags = {
    Name        = "${local.resource_prefix}-ecs-logs"
    Environment = var.environment
  }
}

# --- ECS Cluster, Task Definition, Service ---
resource "aws_ecs_cluster" "main" {
  name = "${local.resource_prefix}-cluster"

  tags = {
    Name        = "${local.resource_prefix}-cluster"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "app_task" {
  family                   = "${local.resource_prefix}-app-task"
  network_mode             = "awsvpc" # Required for Fargate
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.app_cpu
  memory                   = var.app_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn # Role for the application itself

  # Container Definition
  container_definitions = jsonencode([
    {
      name      = "${local.resource_prefix}-container"
      image     = var.app_image_url # Make sure this image exists in ECR!
      cpu       = var.app_cpu       # Can allocate CPU/Memory per container too
      memory    = var.app_memory
      essential = true              # Task stops if this container fails
      portMappings = [
        {
          containerPort = var.app_container_port
          hostPort      = var.app_container_port # Not used in awsvpc mode but required syntactically
          protocol      = "tcp"
        }
      ]
      # --- Logging Configuration ---
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs" # Prefix for log streams
        }
      }
      # --- Environment Variables & Secrets ---
      # Option 1: Inject secrets directly into environment variables via secretsmanager integration
      secrets = [
        {
          name      = "DATABASE_URL_SECRET" # Name for env var holding the secret ARN or full json
          valueFrom = aws_secretsmanager_secret.db_credentials.arn
        }
        # Add other secrets as needed
      ]
      # Option 2: Pass env variables directly (less secure for secrets)
      environment = [
        {
          name  = "DJANGO_SETTINGS_MODULE"
          value = "your_project.settings.production" # Replace with your actual settings module
        },
        {
          name = "AWS_REGION" # Useful for AWS SDKs within the app
          value = var.aws_region
        },
        # Example: Let Django parse DATABASE_URL_SECRET (JSON) from Secrets Manager
        # Your Django settings.py needs logic to parse this JSON env var
        # import json, os
        # db_secret_json = os.environ.get('DATABASE_URL_SECRET')
        # if db_secret_json:
        #    db_creds = json.loads(db_secret_json)
        #    DATABASES = {
        #        'default': {
        #            'ENGINE': 'django.db.backends.postgresql',
        #            'NAME': db_creds['dbName'],
        #            'USER': db_creds['username'],
        #            'PASSWORD': db_creds['password'],
        #            'HOST': db_creds['host'],
        #            'PORT': db_creds['port'],
        #        }
        #    }
      ]
      # Add readiness/health checks if your container framework supports them
      # healthCheck = { ... }
    }
  ])

  tags = {
    Name        = "${local.resource_prefix}-app-task-def"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "app_service" {
  name            = "${local.resource_prefix}-app-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app_task.arn
  desired_count   = var.app_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = module.vpc.private_subnets # Run tasks in private subnets
    security_groups = [aws_security_group.ecs_tasks_sg.id]
    assign_public_ip = false # Fargate tasks in private subnets should not get public IPs
  }

  # Link to Application Load Balancer
  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = "${local.resource_prefix}-container" # Name from container_definitions
    container_port   = var.app_container_port
  }

  # Ensure service waits for ALB to be ready
  depends_on = [aws_lb_listener.https]

  # Auto Scaling configuration depends on aws_appautoscaling_target & aws_appautoscaling_policy below

  # Optional: Configure deployment settings
  deployment_controller {
    type = "ECS" # Rolling updates
  }
  # Optional: Enable deployment circuit breaker
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  # Propagate tags to tasks
  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  tags = {
    Name        = "${local.resource_prefix}-app-service"
    Environment = var.environment
  }

  # Grace period for tasks to deregister from LB during scaling/deployments
  health_check_grace_period_seconds = 60
}

# --- Application Auto Scaling for ECS Service ---
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.app_max_capacity
  min_capacity       = var.app_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale based on CPU Utilization
resource "aws_appautoscaling_policy" "ecs_scale_cpu" {
  name               = "${local.resource_prefix}-scale-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 75.0 # Target CPU utilization percentage
    scale_in_cooldown  = 300  # Seconds before allowing another scale-in
    scale_out_cooldown = 60   # Seconds before allowing another scale-out
  }
}

# Optional: Scale based on Memory Utilization
resource "aws_appautoscaling_policy" "ecs_scale_memory" {
  name               = "${local.resource_prefix}-scale-memory"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 75.0 # Target Memory utilization percentage
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# --- Application Load Balancer (ALB) ---
resource "aws_lb" "main" {
  name               = "${local.resource_prefix}-alb"
  internal           = false # Internet-facing
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = module.vpc.public_subnets # Place ALB in public subnets

  enable_deletion_protection = false # Set to true for production

  tags = {
    Name        = "${local.resource_prefix}-alb"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "app_tg" {
  name        = "${local.resource_prefix}-app-tg"
  port        = var.app_container_port
  protocol    = "HTTP" # ALB talks HTTP to containers, SSL termination at ALB
  target_type = "ip"   # Required for Fargate
  vpc_id      = module.vpc.vpc_id

  health_check {
    enabled             = true
    path                = "/" # Adjust to your app's health check endpoint
    protocol            = "HTTP"
    port                = "traffic-port"
    matcher             = "200-399" # Expect HTTP 2xx or 3xx
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  # Slow start avoids overwhelming new tasks
  slow_start = 60 # seconds

  tags = {
    Name        = "${local.resource_prefix}-app-tg"
    Environment = var.environment
  }
}

# --- ACM Certificate ---
resource "aws_acm_certificate" "cert" {
  domain_name       = local.app_domain_name
  validation_method = "DNS" # Recommended for automation with Route 53

  tags = {
    Name        = "${local.resource_prefix}-cert"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true # Avoid downtime during certificate renewals
  }
}

# --- Route 53 for DNS Validation ---
data "aws_route53_zone" "main" {
  name         = var.domain_name # Your main domain zone
  private_zone = false
}

resource "aws_route53_record" "cert_validation" {
  # Create one record per validation option provided by ACM
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true # Useful if validation records change
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "cert" {
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}


# --- ALB Listeners ---
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action: Redirect HTTP to HTTPS
  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301" # Permanent redirect
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08" # Choose appropriate security policy
  certificate_arn   = aws_acm_certificate_validation.cert.certificate_arn

  # Default action: Forward traffic to the ECS target group
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# --- WAF (Web Application Firewall) - Optional but Recommended ---
resource "aws_wafv2_web_acl" "main" {
  name        = "${local.resource_prefix}-waf"
  description = "WAF ACL for Django application ALB"
  scope       = "REGIONAL" # Use REGIONAL for ALB

  default_action {
    allow {} # Default action is to allow requests that don't match rules
  }

  # Example Rule: AWS Managed Rule Set for common attacks
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {} # Use the actions defined within the rule set
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "waf-${local.resource_prefix}-CommonRules"
      sampled_requests_enabled   = true
    }
  }

  # Example Rule: Block specific IPs (replace with actual IPs if needed)
  # resource "aws_wafv2_ip_set" "blocklist" {
  #   name               = "${local.resource_prefix}-ip-blocklist"
  #   scope              = "REGIONAL"
  #   ip_address_version = "IPV4"
  #   addresses          = ["192.0.2.44/32", "203.0.113.0/24"]
  # }
  # rule {
  #   name     = "IPBlockRule"
  #   priority = 0 # Highest priority

  #   action {
  #     block {} # Block requests matching this rule
  #   }

  #   statement {
  #     ip_set_reference_statement {
  #       arn = aws_wafv2_ip_set.blocklist.arn
  #     }
  #   }
  #   visibility_config {
  #      cloudwatch_metrics_enabled = true
  #      metric_name                = "waf-${local.resource_prefix}-IPBlock"
  #      sampled_requests_enabled   = true
  #   }
  # }


  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "waf-${local.resource_prefix}-main"
    sampled_requests_enabled   = true # Log sampled requests for debugging
  }

  tags = {
    Name        = "${local.resource_prefix}-waf"
    Environment = var.environment
  }
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "alb_assoc" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# --- S3 Bucket for Static Assets ---
resource "aws_s3_bucket" "static_assets" {
  bucket = local.s3_bucket_name
  # acl    = "private" # Recommended: Use bucket policy + OAI instead of ACLs

  tags = {
    Name        = "${local.resource_prefix}-static-assets"
    Environment = var.environment
    Project     = "DjangoApp"
  }
}

resource "aws_s3_bucket_public_access_block" "static_assets_public_block" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- CloudFront Origin Access Identity (OAI) ---
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for ${local.s3_bucket_name}"
}

# --- S3 Bucket Policy to allow CloudFront OAI ---
data "aws_iam_policy_document" "s3_policy" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.static_assets.arn}/*"] # Allow access to objects in the bucket

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.oai.iam_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "static_assets_policy" {
  bucket = aws_s3_bucket.static_assets.id
  policy = data.aws_iam_policy_document.s3_policy.json
}


# --- CloudFront Distribution ---
resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-${local.s3_bucket_name}"

    # Use OAI to access the private S3 bucket
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${local.resource_prefix} static assets"
  default_root_object = "index.html" # Optional: if serving a static site root

  # Aliases (CNAMEs) - e.g., static.example.com
  # aliases = ["static.${var.domain_name}"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${local.s3_bucket_name}"

    forwarded_values {
      query_string = false # Don't cache based on query strings for static assets
      cookies {
        forward = "none" # Don't forward cookies
      }
      headers = [] # Don't forward headers unless needed
    }

    viewer_protocol_policy = "redirect-to-https" # Enforce HTTPS
    min_ttl                = 0
    default_ttl            = 3600  # Cache for 1 hour by default
    max_ttl                = 86400 # Cache for 24 hours maximum
    compress               = true  # Enable gzip/brotli compression
  }

  # Price class controls edge locations used (affects performance and cost)
  price_class = "PriceClass_100" # US, Canada, Europe

  restrictions {
    geo_restriction {
      restriction_type = "none" # No geographic restrictions by default
    }
  }

  viewer_certificate {
    # If using a CNAME like static.example.com, use ACM cert for that domain
    # acm_certificate_arn = aws_acm_certificate.static_cert.arn # Requires separate cert for static domain
    # ssl_support_method = "sni-only"

    # Use default CloudFront certificate if no CNAME is needed
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "${local.resource_prefix}-cdn"
    Environment = var.environment
  }
}

# --- Route 53 Records for ALB and CloudFront ---
resource "aws_route53_record" "app_alias" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.app_domain_name # e.g., app.example.com
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true # Route traffic based on ALB health
  }
}

# Optional: Create alias for CloudFront if using a custom domain (e.g., static.example.com)
# resource "aws_route53_record" "static_alias" {
#   zone_id = data.aws_route53_zone.main.zone_id
#   name    = "static.${var.domain_name}"
#   type    = "A"
#
#   alias {
#     name                   = aws_cloudfront_distribution.s3_distribution.domain_name
#     zone_id                = aws_cloudfront_distribution.s3_distribution.hosted_zone_id
#     evaluate_target_health = false # CloudFront doesn't have health checks in the same way as ALB
#   }
# }


# --- Outputs ---
output "alb_dns_name" {
  value = try(aws_lb.main.dns_name, "N/A")
  description = "alb_dns_name"
}

output "app_url" {
  description = "URL for the application"
  value       = "https://${local.app_domain_name}"
}

output "rds_instance_endpoint" {
  value = try(aws_db_instance.main.endpoint, "N/A")
  description = "rds_instance_endpoint"
}

output "rds_instance_port" {
  value = try(aws_db_instance.main.port, "N/A")
  description = "rds_instance_port"
}

output "ecs_cluster_name" {
  value = try(aws_ecs_cluster.main.name, "N/A")
  description = "ecs_cluster_name"
}

output "ecr_repository_url" {
  value = try(aws_ecr_repository.app_repo.repository_url, "N/A")
  description = "ecr_repository_url"
}

output "static_assets_bucket_name" {
  value = try(aws_s3_bucket.static_assets.bucket, "N/A")
  description = "static_assets_bucket_name"
}

output "cloudfront_distribution_domain" {
  value = try(aws_cloudfront_distribution.s3_distribution.domain_name, "N/A")
  description = "cloudfront_distribution_domain"
}

output "db_credentials_secret_arn" {
  value = try(aws_secretsmanager_secret.db_credentials.arn, "N/A")
  description = "db_credentials_secret_arn"
}