module "alb" {
  source = "../.."

  name               = "switchyard-app"
  subnet_ids         = ["subnet-aaa111", "subnet-bbb222"]
  security_group_ids = ["sg-0123456789abcdef0"]

  listeners = [
    {
      port     = 80
      protocol = "HTTP"
      default_action = {
        type         = "fixed-response"
        status_code  = "200"
        content_type = "text/plain"
        message_body = "ok"
      }
    },
  ]
}
