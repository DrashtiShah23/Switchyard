"""Static guards for alb, listener_rule, and tls modules."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _module_hcl(name: str) -> str:
    module_dir = REPO_ROOT / "terraform" / "modules" / name
    return "\n".join(path.read_text(encoding="utf-8") for path in module_dir.glob("*.tf"))


def test_alb_has_no_nat_zone_or_acm_create() -> None:
    hcl = _module_hcl("alb")
    assert not re.search(r'resource\s+"aws_nat_gateway"', hcl)
    assert not re.search(r'resource\s+"aws_route53_zone"', hcl)
    assert not re.search(r'resource\s+"aws_acm_certificate"', hcl)
    assert 'resource "aws_lb"' in hcl
    assert 'resource "aws_lb_listener"' in hcl


def test_tls_only_attaches_certificate_references() -> None:
    hcl = _module_hcl("tls")
    assert 'resource "aws_lb_listener_certificate"' in hcl
    assert not re.search(r'resource\s+"aws_acm_certificate"', hcl)
    assert not re.search(r'resource\s+"aws_route53_zone"', hcl)


def test_listener_rule_has_no_alb_create() -> None:
    hcl = _module_hcl("listener_rule")
    assert 'resource "aws_lb_listener_rule"' in hcl
    assert not re.search(r'resource\s+"aws_lb"', hcl)


def test_modules_expose_cross_stack_outputs() -> None:
    alb_outputs = (REPO_ROOT / "terraform/modules/alb/outputs.tf").read_text(encoding="utf-8")
    assert 'output "load_balancer_dns_name"' in alb_outputs
    assert 'output "listener_arns_by_port"' in alb_outputs
    tls_outputs = (REPO_ROOT / "terraform/modules/tls/outputs.tf").read_text(encoding="utf-8")
    assert 'output "certificate_arn"' in tls_outputs
