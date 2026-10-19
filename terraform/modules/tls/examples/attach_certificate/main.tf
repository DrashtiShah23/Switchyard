module "tls" {
  source = "../.."

  listener_arn = "arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
  certificate_arn = (
    "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  )
  is_default = false
}
