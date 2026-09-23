from __future__ import annotations

import json

from butler_core import (
    ExecutionStatus,
    PlannerResult,
    PlannerStatus,
    ResolutionResult,
    ResolverDefinition,
    ToolPlan,
)

from wilfred import CapabilityDefinition, DomainDefinition, WilfredRuntime
from wilfred.models import ToolDefinition, ToolPermission
from wilfred.plugins import PluginDefinition


def _plan(
    tool_name: str,
    reason: str,
    *,
    user_authorized: bool = False,
) -> PlannerResult:
    return PlannerResult(
        status=PlannerStatus.SUCCESS,
        duration_ms=0.0,
        plan=ToolPlan(
            tool_name=tool_name,
            arguments={},
            confidence=1.0,
            reason=reason,
            user_authorized=user_authorized,
        ),
    )


def _plugin(
    *,
    plugin_name: str,
    domain_name: str,
    capability_name: str,
    resolver: ResolverDefinition,
    tool_name: str,
    permission: ToolPermission = ToolPermission.READ,
) -> PluginDefinition:
    def register(registry) -> None:
        registry.register(
            ToolDefinition(
                name=tool_name,
                description=f"Test tool {tool_name}.",
                handler=lambda: {"tool": tool_name},
                permission=permission,
            )
        )

    return PluginDefinition(
        name=plugin_name,
        register=register,
        domains=(DomainDefinition(name=domain_name),),
        capabilities=(
            CapabilityDefinition(
                name=capability_name,
                domain=domain_name,
                resolvers=(resolver,),
            ),
        ),
    )


def test_capability_owned_resolver_skips_planner_provider() -> None:
    provider_calls: list[str] = []

    def provider(message, prompt, tools):
        provider_calls.append(message)
        raise AssertionError("planner provider must not be called")

    plugin = _plugin(
        plugin_name="plugin.media",
        domain_name="media",
        capability_name="playback",
        resolver=ResolverDefinition(
            name="media.playback.local",
            handler=lambda message: ResolutionResult.handled_result(
                _plan("play_media", "capability resolver")
            ),
        ),
        tool_name="play_media",
    )

    runtime = WilfredRuntime(
        provider=provider,
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("play locally")

    assert provider_calls == []
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value == {"tool": "play_media"}
    assert result.planning.plan is not None
    assert result.planning.plan.reason == "capability resolver"


def test_capability_resolver_order_is_deterministic() -> None:
    calls: list[str] = []

    def alpha_resolver(message):
        calls.append("alpha")
        return ResolutionResult.not_handled_result()

    def zeta_resolver(message):
        calls.append("zeta")
        return ResolutionResult.handled_result(
            _plan("zeta_tool", "zeta handled")
        )

    alpha = _plugin(
        plugin_name="plugin.alpha",
        domain_name="alpha",
        capability_name="status",
        resolver=ResolverDefinition("alpha.status", alpha_resolver),
        tool_name="alpha_tool",
    )
    zeta = _plugin(
        plugin_name="plugin.zeta",
        domain_name="zeta",
        capability_name="status",
        resolver=ResolverDefinition("zeta.status", zeta_resolver),
        tool_name="zeta_tool",
    )

    runtime = WilfredRuntime(
        provider=lambda *args: (_ for _ in ()).throw(
            AssertionError("planner provider must not be called")
        ),
        system_prompt="Test.",
        plugins=(zeta, alpha),
    )

    result = runtime.execute_goal("status")

    assert calls == ["alpha", "zeta"]
    assert result.execution is not None
    assert result.execution.value == {"tool": "zeta_tool"}


def test_legacy_runtime_resolvers_keep_precedence() -> None:
    capability_calls: list[str] = []

    def capability_resolver(message):
        capability_calls.append(message)
        return ResolutionResult.handled_result(
            _plan("read_state", "capability")
        )

    plugin = _plugin(
        plugin_name="plugin.state",
        domain_name="state",
        capability_name="read",
        resolver=ResolverDefinition("state.read", capability_resolver),
        tool_name="read_state",
    )
    legacy = ResolverDefinition(
        name="legacy.read",
        handler=lambda message: ResolutionResult.handled_result(
            _plan("read_state", "legacy")
        ),
    )

    runtime = WilfredRuntime(
        provider=lambda *args: "{}",
        system_prompt="Test.",
        plugins=(plugin,),
        resolvers=(legacy,),
    )

    result = runtime.execute_goal("read")

    assert capability_calls == []
    assert result.planning.plan is not None
    assert result.planning.plan.reason == "legacy"


def test_capability_decline_preserves_planner_fallback() -> None:
    provider_calls: list[str] = []

    def provider(message, prompt, tools):
        provider_calls.append(message)
        return json.dumps(
            {
                "tool_name": "read_state",
                "arguments": {},
                "confidence": 1.0,
                "reason": "planner fallback",
            }
        )

    plugin = _plugin(
        plugin_name="plugin.state",
        domain_name="state",
        capability_name="read",
        resolver=ResolverDefinition(
            "state.read",
            lambda message: ResolutionResult.not_handled_result(),
        ),
        tool_name="read_state",
    )

    runtime = WilfredRuntime(
        provider=provider,
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("use planner")

    assert provider_calls == ["use planner"]
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS


def test_capability_resolver_cannot_bypass_action_confirmation() -> None:
    plugin = _plugin(
        plugin_name="plugin.action",
        domain_name="action",
        capability_name="run",
        resolver=ResolverDefinition(
            "action.run",
            lambda message: ResolutionResult.handled_result(
                _plan("dangerous_action", "capability action")
            ),
        ),
        tool_name="dangerous_action",
        permission=ToolPermission.ACTION,
    )

    runtime = WilfredRuntime(
        provider=lambda *args: "{}",
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("do it")

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.CONFIRMATION_REQUIRED



def test_trusted_capability_resolver_can_authorize_action() -> None:
    plugin = _plugin(
        plugin_name="plugin.action-authorized",
        domain_name="authorized",
        capability_name="run",
        resolver=ResolverDefinition(
            "authorized.run",
            lambda message: ResolutionResult.handled_result(
                _plan(
                    "authorized_action",
                    "explicit user action",
                    user_authorized=True,
                )
            ),
        ),
        tool_name="authorized_action",
        permission=ToolPermission.ACTION,
    )

    runtime = WilfredRuntime(
        provider=lambda *args: "{}",
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("do it now")

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
    assert result.execution.value == {"tool": "authorized_action"}


def test_planner_cannot_self_authorize_action_with_extra_json_field() -> None:
    def provider(message, prompt, tools):
        return json.dumps(
            {
                "tool_name": "planned_action",
                "arguments": {},
                "confidence": 1.0,
                "reason": "planner action",
                "user_authorized": True,
            }
        )

    plugin = _plugin(
        plugin_name="plugin.planned-action",
        domain_name="planned",
        capability_name="run",
        resolver=ResolverDefinition(
            "planned.run",
            lambda message: ResolutionResult.not_handled_result(),
        ),
        tool_name="planned_action",
        permission=ToolPermission.ACTION,
    )

    runtime = WilfredRuntime(
        provider=provider,
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("do it")

    assert result.planning.plan is not None
    assert result.planning.plan.user_authorized is False
    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.CONFIRMATION_REQUIRED


def test_explicit_runtime_confirmation_remains_supported() -> None:
    plugin = _plugin(
        plugin_name="plugin.confirmed-action",
        domain_name="confirmed",
        capability_name="run",
        resolver=ResolverDefinition(
            "confirmed.run",
            lambda message: ResolutionResult.handled_result(
                _plan("confirmed_action", "needs confirmation")
            ),
        ),
        tool_name="confirmed_action",
        permission=ToolPermission.ACTION,
    )

    runtime = WilfredRuntime(
        provider=lambda *args: "{}",
        system_prompt="Test.",
        plugins=(plugin,),
    )

    result = runtime.execute_goal("do it", confirmed=True)

    assert result.execution is not None
    assert result.execution.status is ExecutionStatus.SUCCESS
