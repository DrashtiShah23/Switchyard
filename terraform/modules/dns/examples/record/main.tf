module "dns" {
  source = "../.."

  zone_id         = "Z3P5QSUBK4LQIN"
  record_name     = "app.example.com"
  record_type     = "A"
  ttl_seconds     = 300
  records         = ["1.2.3.4"]
  allow_overwrite = true
}
