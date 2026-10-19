"""ChangeSpecification → Terraform module input renderer tests."""

from __future__ import annotations

import json

import pytest

from app.domain.enums import LifecycleState
from app.domain.errors import DomainValidationError
from app.domain.normalize import accept_change_request
from app.infrastructure.renderer import ChangeSpecificationRenderer, RenderContext
from tests.unit.conftest import dns_payload, lb_payload, sg_payload, tls_payload

_LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-west-2:123456789012:"
    "listener/app/app-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
)


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
    assert first.variables["records"] == ["1.2.3.4"]


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


def test_render_load_balancer_route(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(lb_payload())
    context = RenderContext(listener_arns={"app-alb:80": _LISTENER_ARN})
    rendered = renderer.render(spec, context=context)
    assert rendered.module_name == "listener_rule"
    assert rendered.variables["listener_arn"] == _LISTENER_ARN
    assert rendered.variables["priority"] == 100
    assert rendered.variables["path_pattern"] == "/health"
    assert rendered.variables["action"]["type"] == "fixed-response"
    assert rendered.variables["action"]["status_code"] == "200"
    assert "hcl" not in json.dumps(rendered.to_dict())


def test_render_load_balancer_route_requires_listener_context(
    renderer: ChangeSpecificationRenderer,
) -> None:
    _, spec = accept_change_request(lb_payload())
    with pytest.raises(DomainValidationError, match="listener_arns"):
        renderer.render(spec, context=RenderContext())


def test_render_tls_binding(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(tls_payload())
    rendered = renderer.render(spec)
    assert rendered.module_name == "tls"
    assert rendered.variables["listener_arn"].startswith("arn:aws:elasticloadbalancing:")
    assert rendered.variables["certificate_arn"].startswith("arn:aws:acm:")
    assert rendered.variables["is_default"] is True


def test_all_four_change_types_render(renderer: ChangeSpecificationRenderer) -> None:
    cases = [
        (
            dns_payload(),
            RenderContext(hosted_zone_id="Z3P5QSUBK4LQIN"),
            "dns",
        ),
        (sg_payload(), RenderContext(), "security_group"),
        (
            lb_payload(),
            RenderContext(listener_arns={"app-alb:80": _LISTENER_ARN}),
            "listener_rule",
        ),
        (tls_payload(), RenderContext(), "tls"),
    ]
    for payload, context, module_name in cases:
        _, spec = accept_change_request(payload)
        rendered = renderer.render(spec, context=context)
        assert rendered.module_name == module_name
        assert rendered.canonical_json() == renderer.render(spec, context=context).canonical_json()


def test_canonical_json_is_stable_key_order(renderer: ChangeSpecificationRenderer) -> None:
    _, spec = accept_change_request(dns_payload())
    rendered = renderer.render(spec, context=RenderContext(hosted_zone_id="Z3P5QSUBK4LQIN"))
    parsed = json.loads(rendered.canonical_json())
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_accept_still_yields_validated_before_render() -> None:
    request, _ = accept_change_request(dns_payload())
    assert request.state is LifecycleState.VALIDATED
