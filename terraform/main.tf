terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.0"
}

provider "aws" {
  region = "us-east-1" # Replace with your desired region
}

# ---------------------------------------------------------------------------------------------------------------------
# NETWORK
# ---------------------------------------------------------------------------------------------------------------------

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "perkolate-vpc"
  }
}

resource "aws_subnet" "public_subnets" {
  count             = 2 # Create two public subnets in different AZs for high availability
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "perkolate-public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private_subnets" {
  count             = 2 # Create two private subnets in different AZs
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 2) # Offset by 2 for the public subnets
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "perkolate-private-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "perkolate-internet-gateway"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "perkolate-public-route-table"
  }
}

resource "aws_route_table_association" "public_subnet_assoc" {
  count          = 2
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

# NAT Gateway (for private subnet outbound internet access - optional)
resource "aws_eip" "nat_gateway" {
  domain   = "vpc"
  depends_on = [aws_internet_gateway.gw]
}

resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = aws_eip.nat_gateway.id
  subnet_id     = aws_subnet.public_subnets[0].id

  tags = {
    Name = "perkolate-nat-gateway"
  }

  depends_on = [aws_internet_gateway.gw]
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gateway.id
  }

  tags = {
    Name = "perkolate-private-route-table"
  }
}

resource "aws_route_table_association" "private_subnet_assoc" {
  count          = 2
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_rt.id
}

# ---------------------------------------------------------------------------------------------------------------------
# SECURITY GROUPS
# ---------------------------------------------------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "perkolate-alb-sg"
  description = "Security group for the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow HTTP from anywhere
  }

   ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow HTTPS from anywhere
  }


  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "perkolate-alb-sg"
  }
}

resource "aws_security_group" "ec2" {
  name        = "perkolate-ec2-sg"
  description = "Security group for the EC2 instances"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000 # Django's default port
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [aws_security_group.alb.id] # Allow traffic from the ALB
  }

  ingress {
    from_port   = 22 # SSH access - restrict to your IP address in production!
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # REMOVE FOR PRODUCTION AND RESTRICT TO YOUR IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "perkolate-ec2-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "perkolate-rds-sg"
  description = "Security group for the RDS instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432 # PostgreSQL port
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [aws_security_group.ec2.id] # Allow traffic from the EC2 instances
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "perkolate-rds-sg"
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# RDS
# ---------------------------------------------------------------------------------------------------------------------

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "perkolate-rds-subnet-group"
  subnet_ids = aws_subnet.private_subnets.*.id

  tags = {
    Name = "perkolate-rds-subnet-group"
  }
}

resource "aws_rds_cluster" "default" {
  cluster_identifier      = "perkolate-db-cluster"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = "15.3"
  master_username         = "admin"
  master_password         = "your_secure_password" # Replace with a secure password
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  skip_final_snapshot     = true
  backup_retention_period = 5
  preferred_backup_window = "07:00-09:00"
  availability_zones      = data.aws_availability_zones.available.names
  storage_encrypted = true
  apply_immediately = true

  tags = {
    Name = "perkolate-db-cluster"
  }
}

resource "aws_rds_cluster_instance" "cluster_instances" {
  count              = 2 # Create 2 instances for high availability
  cluster_identifier = aws_rds_cluster.default.id
  instance_class     = "db.t3.medium"
  engine             = "aurora-postgresql"
  engine_version     = "15.3"
  publicly_accessible = false

  tags = {
    Name = "perkolate-db-instance-${count.index + 1}"
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# LOAD BALANCER
# ---------------------------------------------------------------------------------------------------------------------

resource "aws_lb" "alb" {
  name               = "perkolate-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public_subnets.*.id

  tags = {
    Name = "perkolate-alb"
  }
}

resource "aws_lb_target_group" "tg" {
  name     = "perkolate-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path               = "/" # Or your application's health check endpoint
    protocol           = "HTTP"
    matcher            = "200-399"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_acm_certificate" "cert" {
  domain_name       = "yourdomain.com" # Replace with your domain
  validation_method = "DNS" # or EMAIL

  tags = {
    Name = "perkolate-certificate"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

# Assuming you've configured Route53 for your domain (yourdomain.com)
# resource "aws_route53_record" "alb" {
#   zone_id = "YOUR_ROUTE53_ZONE_ID"  # Replace with your Route 53 zone ID
#   name    = "yourdomain.com" # Replace with your domain
#   type    = "A"

#   alias {
#     name                   = aws_lb.alb.dns_name
#     zone_id                = aws_lb.alb.zone_id
#     evaluate_target_health = true
#   }
# }

# ---------------------------------------------------------------------------------------------------------------------
# EC2 INSTANCES & AUTO SCALING
# ---------------------------------------------------------------------------------------------------------------------

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_launch_template" "ec2" {
  name_prefix   = "perkolate-launch-template-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"

  network_interface {
    security_groups = [aws_security_group.ec2.id]
    subnet_id       = aws_subnet.private_subnets[0].id # Place in a private subnet
  }

  user_data = base64encode(<<EOF
#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip nginx
pip3 install django gunicorn psycopg2-binary
# Configure your Django project here (e.g., clone from Git, collectstatic, etc.)
# Example (replace with your actual repo and configuration):
git clone https://github.com/yourusername/your-django-project.git /home/ubuntu/perkolate
cd /home/ubuntu/perkolate
python3 manage.py migrate
python3 manage.py collectstatic --noinput
gunicorn --bind 0.0.0.0:8000 perkolate.wsgi --daemon
#Configure nginx
echo "server {
    listen 80;
    server_name yourdomain.com; #Replace with your domain or public IP

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/perkolate;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}" > /etc/nginx/sites-available/perkolate
ln -s /etc/nginx/sites-available/perkolate /etc/nginx/sites-enabled
nginx -t
systemctl restart nginx
EOF
  )

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "perkolate-ec2-instance"
    }
  }
}

resource "aws_autoscaling_group" "asg" {
  name                      = "perkolate-asg"
  desired_capacity        = 2
  max_size                  = 4
  min_size                  = 2
  vpc_zone_identifier       = aws_subnet.private_subnets.*.id
  target_group_arns         = [aws_lb_target_group.tg.arn]

  launch_template {
    id      = aws_launch_template.ec2.id
    version = "$Latest"
  }

  health_check_type         = "ELB"
  health_check_grace_period = 300 # Seconds

  tags = [
    {
      key                 = "Name"
      value               = "perkolate-ec2-instance"
      propagate_at_launch = true
    },
  ]
}

# CloudWatch Metric Alarm for Scaling (example based on CPU utilization)
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "perkolate-cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 70  # Scale up if CPU utilization exceeds 70%
  alarm_description   = "Alarm when server CPU exceeds 70%"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.asg.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_up.arn]
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "perkolate-cpu-low"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 30  # Scale down if CPU utilization drops below 30%
  alarm_description   = "Alarm when server CPU is below 30%"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.asg.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_down.arn]
}

resource "aws_autoscaling_policy" "scale_up" {
  name                      = "perkolate-scale-up"
  scaling_adjustment        = 1 # Add one instance
  adjustment_type           = "ChangeInCapacity"
  cooldown                  = 300
  autoscaling_group_name = aws_autoscaling_group.asg.name
}

resource "aws_autoscaling_policy" "scale_down" {
  name                      = "perkolate-scale-down"
  scaling_adjustment        = -1 # Remove one instance
  adjustment_type           = "ChangeInCapacity"
  cooldown                  = 300
  autoscaling_group_name = aws_autoscaling_group.asg.name
}

data "aws_availability_zones" "available" {}

output "alb_dns_name" {
  value = aws_lb.alb.dns_name
  description = "The DNS name of the ALB"
}