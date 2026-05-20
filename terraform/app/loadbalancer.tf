resource "aws_lb" "this" {
  name               = "aws-app-alb"
  subnets            = aws_subnet.public.*.id
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb.id]

  tags = merge(
    local.common_tags,
    { Name = "aws-app-alb" }
  )
}

resource "aws_lb_listener" "http_forward" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_lb_target_group" "this" {
  name        = "aws-app-alb-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    healthy_threshold   = "3"
    interval            = "90"
    protocol            = "HTTP"
    matcher             = "200-299"
    timeout             = "20"
    path                = "/"
    unhealthy_threshold = "2"
  }
}

resource "aws_lb" "client" {
  name               = "streamlit-dashboard-alb"
  subnets            = aws_subnet.public.*.id
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb.id]

  tags = merge(
    local.common_tags,
    { Name = "streamlit-dashboard-alb" }
  )
}

resource "aws_lb_listener" "client_http_forward" {
  load_balancer_arn = aws_lb.client.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.client.arn
  }
}

resource "aws_lb_target_group" "client" {
  name        = "streamlit-dashboard-alb-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  health_check {
    healthy_threshold   = "3"
    interval            = "90"
    protocol            = "HTTP"
    matcher             = "200-299"
    timeout             = "20"
    path                = "/"
    unhealthy_threshold = "2"
  }
}

/*
resource "aws_lb_listener_rule" "client_routing" {
  listener_arn = aws_lb_listener.http_forward.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.client.arn
  }

  condition {
    path_pattern {
      values = ["/client"]
    }
  }
}
*/

output "api_lb_dns_name" {
  value = aws_lb.this.dns_name
}

output "client_lb_dns_name" {
  value = aws_lb.client.dns_name
}
