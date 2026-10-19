locals {
  base_tags = merge(
    {
      Project   = "switchyard"
      Component = "listener_rule"
      ManagedBy = "terraform"
    },
    var.tags,
  )
}

resource "aws_lb_listener_rule" "this" {
  listener_arn = var.listener_arn
  priority     = var.priority

  dynamic "condition" {
    for_each = var.path_pattern != null ? [var.path_pattern] : []
    content {
      path_pattern {
        values = [condition.value]
      }
    }
  }

  dynamic "condition" {
    for_each = var.host_header != null ? [var.host_header] : []
    content {
      host_header {
        values = [condition.value]
      }
    }
  }

  dynamic "action" {
    for_each = var.action.type == "fixed-response" ? [var.action] : []
    content {
      type = "fixed-response"
      fixed_response {
        content_type = coalesce(action.value.content_type, "text/plain")
        message_body = coalesce(action.value.message_body, "ok")
        status_code  = action.value.status_code
      }
    }
  }

  dynamic "action" {
    for_each = var.action.type == "forward" ? [var.action] : []
    content {
      type             = "forward"
      target_group_arn = action.value.target_group_arn
    }
  }

  tags = local.base_tags
}
