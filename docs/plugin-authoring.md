# Plugin authoring guide

Wilfred plugins package integrations, executable tools and semantic behavior without moving provider-specific knowledge into Butler Core.

The built-in `demo.echo` plugin is the reference implementation. It is intentionally dependency-free, but it models the same ownership boundaries expected from a real integration:

`provider → plugin → domain → capability → resolver → tool`

The public [Home Assistant Plugin](https://github.com/keriol/home-assistant-plugin)
is the first real smart-home integration built around this model. It began as a
concrete Wilfred proving example and is now evolving toward a consumer-neutral
Butler plugin that can be loaded by independent sibling runtimes. That evolution
is useful evidence that the plugin contract should describe the integration,
not bind it permanently to one host runtime.

## Ownership model

Each layer has one job.

- **Provider / integration** connects to or adapts an external service. In the reference plugin, `EchoProvider` is the provider boundary and `LocalEchoProvider` is the dependency-free example implementation.
- **Plugin** packages everything that belongs together and declares what it contributes to a Butler runtime.
- **Domain** owns related knowledge and behavior. The reference plugin declares the `demo` domain.
- **Capability** names something the Butler knows how to do inside that domain. The reference plugin declares `demo.echo`.
- **Resolver** deterministically recognizes goals that the capability can handle and produces a normal tool plan. The reference resolver is `demo.echo.text`.
- **Tool** is the typed executable operation. The reference tool is `demo_echo` and is classified `READ`.
- **Verification contribution** declares behavior that the plugin promises should remain true. Wilfred owns the harness that executes those expectations.

The capability registry and tool registry remain separate. Semantic ownership does not make a capability executable by itself, and executable tools do not implicitly define semantic ownership.

## Reference implementation

The provider boundary is explicit even though the example does not need a network service:

```python
class EchoProvider(Protocol):
    def echo(self, message: str) -> str:
        ...


class LocalEchoProvider:
    def echo(self, message: str) -> str:
        return message
```

The tool delegates provider-specific work through that boundary:

```python
def echo_message(message: str) -> dict[str, str]:
    return {"message": _provider.echo(message)}
```

The domain and capability declare semantic ownership:

```python
demo_domain = DomainDefinition(
    name="demo",
    description="Dependency-free examples for Wilfred plugin authors.",
)

demo_echo_capability = CapabilityDefinition(
    name="echo",
    domain="demo",
    resolvers=(
        ResolverDefinition(
            name="demo.echo.text",
            handler=resolve_demo_echo,
        ),
    ),
)
```

The resolver handles only goals it recognizes. Otherwise it returns `NOT_HANDLED`, preserving planner fallback:

```python
def resolve_demo_echo(message: str) -> ResolutionResult:
    if not message.strip().lower().startswith("echo "):
        return ResolutionResult.not_handled_result()

    return ResolutionResult.handled_result(
        PlannerResult(
            status=PlannerStatus.SUCCESS,
            duration_ms=0.0,
            plan=ToolPlan(
                tool_name="demo_echo",
                arguments={"message": message[5:].strip()},
                confidence=1.0,
                reason="demo.echo deterministic resolver",
            ),
        )
    )
```

The same plugin can declare deterministic verification expectations without embedding pytest or arbitrary executable test callbacks:

```python
demo_echo_expectation = GoalExpectation(
    identity="demo.echo.basic",
    goal="echo hello from verification",
    capability="demo.echo",
    tool_name="demo_echo",
    expected_arguments={
        "message": "hello from verification",
    },
    expected_value={
        "message": "hello from verification",
    },
    verify_value=True,
)
```

Finally the plugin declares executable, semantic and verification contributions together:

```python
plugin = PluginDefinition(
    name="demo.echo",
    register=register_demo_echo_tools,
    domains=(demo_domain,),
    capabilities=(demo_echo_capability,),
    verification=(demo_echo_expectation,),
)
```

## Load and inspect the plugin

The reference plugin is included in the normal Wilfred distribution and can be discovered like any other public plugin:

```python
from wilfred import ToolRegistry, discover_plugins, load_plugins

registry = ToolRegistry()
plugins = discover_plugins(["wilfred.plugins.demo_echo"])
results = load_plugins(registry, plugins)

assert results[0].tool_names == ("demo_echo",)
assert results[0].domain_names == ("demo",)
assert results[0].capability_names == ("demo.echo",)
```

Use `WilfredRuntime` when you want capability-owned resolvers to participate in deterministic goal resolution:

```python
from wilfred import WilfredRuntime, discover_plugins

plugins = discover_plugins(["wilfred.plugins.demo_echo"])

runtime = WilfredRuntime(
    provider=planner_provider,
    system_prompt="You are a Butler runtime.",
    plugins=plugins,
)

result = runtime.execute_goal("echo hello")
```

`demo.echo.text` resolves the goal before planner fallback, but the resulting `demo_echo` tool still executes through the normal Execution Engine and permission policy.

## Verify declared expectations

Verification declarations describe expected behavior. They do not execute during plugin import or normal runtime composition.

A shared harness collects them from the loaded plugin set and executes deterministic goals through the normal `WilfredRuntime` path:

```python
from wilfred import discover_plugins, verify_plugins

plugins = discover_plugins(["wilfred.plugins.demo_echo"])
results = verify_plugins(plugins)

assert results[0].passed is True
```

Each `VerificationResult` contains the expectation ID, plugin name, PASS/FAIL state and deterministic diagnostics. Duplicate expectation identities within one plugin are rejected when the `PluginDefinition` is constructed. Expectations must reference capabilities owned by that same plugin.

This first public contract is intentionally provider-neutral and goal-level. Frontend-specific regression data belongs to the frontend that owns it. A future Alexa frontend, for example, may compose utterance expectations with the same principle without introducing Alexa intents, slots or SMAPI concepts into Butler Core or Wilfred's provider-neutral runtime.

## Authoring rules

Keep these boundaries stable when creating a real plugin:

1. Keep service authentication, clients and transport details in the provider/integration layer.
2. Register typed executable operations as tools with the correct permission classification.
3. Declare semantic ownership explicitly with domains and capabilities.
4. Put deterministic recognition beside the capability that owns it.
5. Return `NOT_HANDLED` when the resolver cannot confidently own a goal.
6. Never bypass Execution Engine policy, confirmation or post-action verification from a resolver.
7. Declare representative deterministic expectations instead of embedding test-framework execution in plugin import paths.
8. Keep frontend presentation and provider-specific rendering outside Butler Core.
9. Do not put secrets, private endpoints or deployment-specific identifiers in public plugin metadata or verification declarations.
10. Keep the plugin dependent on provider-neutral Butler contracts where possible rather than on one sibling runtime merely because that runtime was its first consumer.

## Testing a plugin

A useful plugin test set should prove at least:

- discovery returns the intended `PluginDefinition`;
- tools register deterministically;
- domain and capability identities are reported by `PluginLoadResult`;
- deterministic goals resolve through capability-owned resolvers;
- declared verification expectations pass through the shared harness;
- expectation mismatches produce structured failures;
- unhandled goals preserve planner fallback;
- ACTION or DANGEROUS tools still require the normal policy/confirmation path;
- installation from a built wheel works in a clean environment.

Wilfred's own plugin, capability resolver, verification and clean-room distribution tests exercise those boundaries for the reference plugin.

## From the reference plugin to a real integration

Replace `LocalEchoProvider` with a provider adapter that owns the actual external-service connection. Keep the rest of the shape intact:

`external service → provider adapter → plugin package → domain/capability → resolver → typed tool → Execution Engine`

The Home Assistant Plugin is a real consumer of the same public model, but it is intentionally not used as the small authoring example so the reference remains installable and independent of any particular home-automation platform.

The architectural lesson from HAP is broader than Home Assistant. If a user wants to integrate another home-automation manager, the preferred direction is another dedicated plugin:

```text
Butler runtime
    |
    +-> Home Assistant Plugin -> Home Assistant
    |
    +-> Platform X Plugin     -> Platform X
```

Each platform plugin owns its authentication, transport and platform-specific
operations. Butler Core stays provider-neutral, and the host runtime does not
need platform-specific device APIs baked into its own code.

HAP is currently being migrated toward that fully consumer-neutral boundary.
Do not infer completed dependency changes from this design note; use the HAP
repository and GitHub Issues for current implementation evidence.

For the detailed semantic contracts and deterministic ordering rules, see [Capability and domain contracts](capability-domain-contracts.md).
