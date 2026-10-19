locals {
  base_tags = merge(
    {
      Project   = "switchyard"
      Component = "alb"
      ManagedBy = "terraform"
    },
    var.tags,
  )

  listeners = {
    for idx, listener in var.listeners : tostring(idx) => listener
  }
}

resource "aws_lb" "this" {
  name               = var.name
  internal           = var.internal
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids
  idle_timeout       = var.idle_timeout_seconds

  # Drop protection off for disposable optional sandboxes; env roots may override via forks.
  enable_deletion_protection = false

  tags = merge(local.base_tags, {
    Name = var.name
  })
}

resource "aws_lb_listener" "this" {
  for_each = local.listeners

  load_balancer_arn = aws_lb.this.arn
  port              = each.value.port
  protocol          = each.value.protocol
  certificate_arn   = try(each.value.certificate_arn, null)
  ssl_policy        = try(each.value.ssl_policy, null)

  dynamic "default_action" {
    for_each = each.value.default_action.type == "fixed-response" ? [each.value.default_action] : []
    content {
      type = "fixed-response"
      fixed_response {
        content_type = coalesce(default_action.value.content_type, "text/plain")
        message_body = coalesce(default_action.value.message_body, "ok")
        status_code  = default_action.value.status_code
      }
    }
  }

  dynamic "default_action" {
    for_each = each.value.default_action.type == "forward" ? [each.value.default_action] : []
    content {
      type             = "forward"
      target_group_arn = default_action.value.target_group_arn
    }
  }

  tags = local.base_tags
}

# Intentionally absent: aws_nat_gateway, aws_route53_zone, aws_acm_certificate.
# Target groups are referenced for forward actions, not created here, unless an
# environment chooses to compose a separate target-group module later.
