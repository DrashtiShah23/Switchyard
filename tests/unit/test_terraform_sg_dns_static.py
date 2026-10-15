"""Static guards for security_group and dns modules."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SG_MODULE = REPO_ROOT / "terraform" / "modules" / "security_group"
DNS_MODULE = REPO_ROOT / "terraform" / "modules" / "dns"


def _module_hcl(module_dir: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in module_dir.glob("*.tf"))


def test_security_group_module_has_no_nat_or_alb() -> None:
    hcl = _module_hcl(SG_MODULE)
    assert not re.search(r'resource\s+"aws_nat_gateway"', hcl)
    assert not re.search(r'resource\s+"aws_lb"', hcl)
    assert not re.search(r'resource\s+"aws_eip"', hcl)


def test_dns_module_does_not_create_hosted_zones() -> None:
    hcl = _module_hcl(DNS_MODULE)
    assert not re.search(r'resource\s+"aws_route53_zone"', hcl)
    assert 'resource "aws_route53_record"' in hcl


def test_modules_have_no_environment_constants() -> None:
    for module_dir in (SG_MODULE, DNS_MODULE):
        hcl = _module_hcl(module_dir)
        for forbidden in ('"dev"', '"staging"', '"prod"', "switchyard-dev"):
            assert forbidden not in hcl


def test_security_group_exposes_id_output() -> None:
    outputs = (SG_MODULE / "outputs.tf").read_text(encoding="utf-8")
    assert 'output "security_group_id"' in outputs


def test_dns_exposes_fqdn_output() -> None:
    outputs = (DNS_MODULE / "outputs.tf").read_text(encoding="utf-8")
    assert 'output "fqdn"' in outputs
