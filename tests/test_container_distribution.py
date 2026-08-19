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


def test_reference_binding_is_loopback_only() -> None:
    compose = read("compose.yaml")

    assert (
        "WILFRED_BIND_ADDRESS:-127.0.0.1"
        in compose
    )


def test_distribution_bom_matches_release_baseline() -> None:
    with (
        ROOT / "distribution" / "bom.toml"
    ).open("rb") as stream:
        bom = tomllib.load(stream)

    assert bom["schema_version"] == 1
    assert (
        bom["components"]["butler_core"]["version"]
        == "0.1.4"
    )
    assert (
        bom["components"]["wilfred"]["version"]
        == "0.2.1"
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

