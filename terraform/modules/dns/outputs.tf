output "fqdn" {
  description = "FQDN of the managed record."
  value       = aws_route53_record.this.fqdn
}

output "name" {
  description = "Name of the managed record."
  value       = aws_route53_record.this.name
}

output "type" {
  description = "Type of the managed record."
  value       = aws_route53_record.this.type
}

output "zone_id" {
  description = "Hosted zone id used for the record."
  value       = aws_route53_record.this.zone_id
}

output "records" {
  description = "Record values."
  value       = aws_route53_record.this.records
}
