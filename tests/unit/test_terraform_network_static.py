"""Static checks for the Milestone 4 network Terraform module (zero-cost)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
NETWORK_MODULE = REPO_ROOT / "terraform" / "modules" / "network"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate_terraform.sh"


def _read_module_hcl() -> str:
    parts: list[str] = []
    for path in NETWORK_MODULE.glob("*.tf"):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_network_module_has_no_nat_gateway_resources() -> None:
    hcl = _read_module_hcl()
    assert not re.search(r'resource\s+"aws_nat_gateway"', hcl)
    assert not re.search(r'resource\s+"aws_eip"', hcl)


def test_network_module_has_no_environment_constants() -> None:
    hcl = _read_module_hcl()
    # Environment selection belongs in terraform/environments/*, not the module.
    for forbidden in ('"dev"', '"staging"', '"prod"', "switchyard-dev", "switchyard-prod"):
        assert forbidden not in hcl


def test_network_module_exposes_expected_outputs() -> None:
    outputs = (NETWORK_MODULE / "outputs.tf").read_text(encoding="utf-8")
    for name in (
        "vpc_id",
        "public_subnet_ids",
        "private_subnet_ids",
        "nat_gateway_ids",
        "public_route_table_id",
    ):
        assert f'output "{name}"' in outputs


def test_environment_roots_compose_network_module() -> None:
    for env in ("dev", "staging", "prod"):
        main = REPO_ROOT / "terraform" / "environments" / env / "main.tf"
        text = main.read_text(encoding="utf-8")
        assert 'source = "../../modules/network"' in text
        assert "aws_nat_gateway" not in text


@pytest.mark.skipif(shutil.which("terraform") is None, reason="terraform not installed")
def test_validate_terraform_script_passes() -> None:
    result = subprocess.run(
        ["bash", str(VALIDATE_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
