from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(
        encoding="utf-8"
    )


def test_dockerfile_uses_non_root_runtime() -> None:
    dockerfile = read("Dockerfile")

    assert "FROM python:3.12-slim" in dockerfile
    assert "USER wilfred" in dockerfile
    assert 'ENTRYPOINT ["wilfred"]' in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/var/run/docker.sock" not in dockerfile


def test_development_line_consumes_independent_hap() -> None:
    pyproject = read("pyproject.toml")
    dockerfile = read("Dockerfile")

    assert 'version = "0.2.3.dev0"' in pyproject
    assert (
        "827bbac1038b6591f88648e5b69e50ae66834c19"
        in pyproject
    )
    assert "butler-home-assistant" in dockerfile
    assert "home-assistant-plugin/archive/${HAP_REF}.tar.gz" in dockerfile
    assert "wilfred-home-assistant @" not in dockerfile
    assert "ARG HAP_REF=d1856791b887c36e54c71fe3e81646f969249885" in dockerfile


def test_compose_keeps_runtime_hardened() -> None:
    compose = read("compose.yaml")

    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
    assert "- ALL" in compose
    assert ":/config:ro" in compose
    assert "/var/run/docker.sock" not in compose
    assert (
        "wilfred_home_assistant.bootstrap:"
        "create_plugin_from_environment"
    ) in compose
    assert "wilfred:0.2.3.dev0" in compose
    assert "HAP_REF" in compose


def test_reference_binding_is_loopback_only() -> None:
    compose = read("compose.yaml")

    assert (
        "WILFRED_BIND_ADDRESS:-127.0.0.1"
        in compose
    )


def test_distribution_bom_matches_release_baseline() -> None:
    current_path = ROOT / "distribution" / "bom.toml"
    snapshot_path = (
        ROOT / "distribution" / "releases" / "0.2.2.toml"
    )

    assert current_path.read_bytes() == snapshot_path.read_bytes()

    with current_path.open("rb") as stream:
        bom = tomllib.load(stream)

    assert bom["schema_version"] == 2
    assert bom["release"] == "0.2.2"
    assert bom["source_tag"] == "v0.2.2"
    assert (
        bom["components"]["butler_core"]["version"]
        == "0.2.0"
    )
    assert (
        bom["components"]["butler_core"]["sha256"]
        == "40e18d5ef5792c9c5dad807287ae6717e6a0ba0833751503c2ab06c9c2405736"
    )
    assert (
        bom["components"]["wilfred"]["version"]
        == "0.2.2"
    )
    assert (
        bom["components"]["home_assistant"]["version"]
        == "0.1.0.dev0"
    )

    plugin_ref = (
        bom["components"]["home_assistant"]["git_ref"]
    )

    assert len(plugin_ref) == 40
    int(plugin_ref, 16)

    assert bom["release_scope"]["base_tag"] == "v0.2.1"
    assert "WILF-063" in bom["release_scope"]["issues"]
    assert "WILF-064" in bom["release_scope"]["issues"]


def test_previous_release_bom_snapshots_are_preserved() -> None:
    releases = ROOT / "distribution" / "releases"

    with (releases / "0.2.0.toml").open("rb") as stream:
        bom_020 = tomllib.load(stream)
    with (releases / "0.2.1.toml").open("rb") as stream:
        bom_021 = tomllib.load(stream)

    assert bom_020["components"]["wilfred"]["version"] == "0.2.0"
    assert bom_020["components"]["butler_core"]["version"] == "0.1.3"
    assert bom_021["components"]["wilfred"]["version"] == "0.2.1"
    assert bom_021["components"]["butler_core"]["version"] == "0.1.4"


def test_examples_contain_no_credentials() -> None:
    env_example = read(
        "distribution/env.example"
    )

    assert "WILFRED_OPENAI_API_KEY=\n" in env_example
    assert "WILFRED_HOME_ASSISTANT_TOKEN=\n" in env_example


def test_runtime_checkout_is_reusable() -> None:
    checkout = ROOT / "distribution" / "verify_runtime.py"

    assert checkout.is_file()

    text = checkout.read_text(
        encoding="utf-8"
    )

    assert "/health" in text
    assert "/v1/runtime" in text
    assert "/v1/tools" in text
    assert "home_assistant_get_state" in text
    assert "home_assistant_call_action" in text


def test_container_ci_verifies_registry_pull() -> None:
    workflow = read(
        ".github/workflows/container.yml"
    )

    assert "docker push" in workflow
    assert "docker image rm" in workflow
    assert "docker pull" in workflow
    assert "verify_runtime.py" in workflow
    assert "HAP_REF=d1856791b887c36e54c71fe3e81646f969249885" in workflow
