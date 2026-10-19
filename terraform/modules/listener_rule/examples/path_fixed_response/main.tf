module "listener_rule" {
  source = "../.."

  listener_arn = "arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
  priority     = 100
  path_pattern = "/health"

  action = {
    type         = "fixed-response"
    status_code  = "200"
    content_type = "text/plain"
    message_body = "ok"
  }
}
