"""ChangeSpecification → Terraform module input renderer tests."""

from __future__ import annotations

import json

import pytest

from app.domain.enums import LifecycleState
from app.domain.errors import DomainValidationError
from app.domain.normalize import accept_change_request
from app.infrastructure.renderer import (
    ChangeSpecificationRenderer,
    RenderContext,
    UnsupportedChangeForRenderer,
)
from tests.unit.conftest import dns_payload, lb_payload, sg_payload, tls_payload


@pytest.fixture
def renderer() -> ChangeSpecificationRenderer:
    return ChangeSpecificationRenderer()


def test_render_dns_deterministic(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(dns_payload())
    context = RenderContext(hosted_zone_id="Z3P5QSUBK4LQIN")
    first = renderer.render(spec, context=context)
    second = renderer.render(spec, context=context)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.module_name == "dns"
    assert first.variables["zone_id"] == "Z3P5QSUBK4LQIN"
    assert first.variables["record_type"] == "A"
    assert first.variables["records"] == ["1.2.3.4"]
    assert first.variables["allow_overwrite"] is False
    assert "hcl" not in first.to_dict()


def test_render_dns_update_sets_allow_overwrite(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(dns_payload(change={"action": "update"}))
    rendered = renderer.render(spec, context=RenderContext(hosted_zone_id="Z3P5QSUBK4LQIN"))
    assert rendered.variables["allow_overwrite"] is True


def test_render_dns_requires_zone_context(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(dns_payload())
    with pytest.raises(DomainValidationError, match="hosted_zone_id"):
        renderer.render(spec, context=RenderContext())


def test_render_sg_rule_attach_mode(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(sg_payload())
    rendered = renderer.render(spec)
    assert rendered.module_name == "security_group"
    assert rendered.variables["create_security_group"] is False
    assert rendered.variables["existing_security_group_id"] == "sg-0123456789abcdef0"
    assert rendered.variables["ingress_rules"][0]["cidr_ipv4"] == "10.0.0.0/8"
    assert rendered.variables["ingress_rules"][0]["protocol"] == "tcp"
    assert rendered.variables["egress_rules"] == []


def test_render_sg_maps_all_protocol(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(
        sg_payload(
            change={
                "protocol": "all",
                "from_port": None,
                "to_port": None,
                "cidr_blocks": ["10.0.0.0/8"],
            }
        )
    )
    rendered = renderer.render(spec)
    assert rendered.variables["ingress_rules"][0]["protocol"] == "-1"


def test_render_rejects_lb_and_tls_in_m5(renderer: ChangeSpecificationRenderer) -> None:
    _, lb_spec = accept_change_request(lb_payload())
    _, tls_spec = accept_change_request(tls_payload())
    with pytest.raises(UnsupportedChangeForRenderer):
        renderer.render(lb_spec)
    with pytest.raises(UnsupportedChangeForRenderer):
        renderer.render(tls_spec)


def test_canonical_json_is_stable_key_order(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(dns_payload())
    rendered = renderer.render(spec, context=RenderContext(hosted_zone_id="Z3P5QSUBK4LQIN"))
    parsed = json.loads(rendered.canonical_json())
    assert list(parsed.keys()) == sorted(parsed.keys())
    assert spec.change_spec_id.startswith("spec_")


def test_accept_still_yields_validated_before_render() -> None:
    request, _ = accept_change_request(dns_payload())
    assert request.state is LifecycleState.VALIDATED
