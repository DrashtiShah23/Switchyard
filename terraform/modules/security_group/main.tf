locals {
  base_tags = merge(
    {
      Project   = "switchyard"
      Component = "security_group"
      ManagedBy = "terraform"
    },
    var.tags,
  )

  security_group_id = (
    var.create_security_group
    ? aws_security_group.this[0].id
    : var.existing_security_group_id
  )

  ingress_map = {
    for idx, rule in var.ingress_rules : tostring(idx) => rule
  }

  egress_map = {
    for idx, rule in var.egress_rules : tostring(idx) => rule
  }
}

resource "aws_security_group" "this" {
  count = var.create_security_group ? 1 : 0

  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  tags = merge(local.base_tags, {
    Name = var.name
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "this" {
  for_each = local.ingress_map

  security_group_id = local.security_group_id
  description       = each.value.description
  ip_protocol       = each.value.protocol
  from_port         = try(each.value.from_port, null)
  to_port           = try(each.value.to_port, null)
  # Pass through only one source attribute so the AWS provider schema is satisfied
  # when inputs are valid. Dual-source inputs are rejected by check.rules_have_exactly_one_source.
  cidr_ipv4 = try(each.value.cidr_ipv4, null)
  referenced_security_group_id = try(each.value.cidr_ipv4, null) == null ? try(
    each.value.referenced_security_group_id,
    null
  ) : null

  tags = local.base_tags
}

resource "aws_vpc_security_group_egress_rule" "this" {
  for_each = local.egress_map

  security_group_id = local.security_group_id
  description       = each.value.description
  ip_protocol       = each.value.protocol
  from_port         = try(each.value.from_port, null)
  to_port           = try(each.value.to_port, null)
  cidr_ipv4         = try(each.value.cidr_ipv4, null)
  referenced_security_group_id = try(each.value.cidr_ipv4, null) == null ? try(
    each.value.referenced_security_group_id,
    null
  ) : null

  tags = local.base_tags
}
