from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wilfred import (
    ConfigurationError,
    load_config,
)
from wilfred.__main__ import main


class WilfredConfigurationTests(unittest.TestCase):
    def test_defaults_start_wilfred(self) -> None:
        config = load_config(
            environ={},
            cli_overrides={},
        )

        self.assertEqual(
            config.identity.name,
            "Wilfred",
        )
        self.assertEqual(
            config.identity.locale,
            "en",
        )
        self.assertEqual(
            config.log_level,
            "INFO",
        )

    def test_default_loader_reads_environment(self) -> None:
        with patch.dict(
            os.environ,
            {
                "WILFRED_NAME": "Environment Wilfred",
                "WILFRED_LOCALE": "it-IT",
                "WILFRED_LOG_LEVEL": "debug",
            },
            clear=True,
        ):
            config = load_config(
                cli_overrides={},
            )

        self.assertEqual(
            config.identity.name,
            "Environment Wilfred",
        )
        self.assertEqual(
            config.identity.locale,
            "it-IT",
        )
        self.assertEqual(
            config.log_level,
            "DEBUG",
        )

    def test_configuration_file_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wilfred.toml"
            path.write_text(
                """
[identity]
name = "Public Butler"
locale = "it-IT"

[runtime]
log_level = "warning"
""".strip(),
                encoding="utf-8",
            )

            config = load_config(
                config_file=path,
                environ={},
                cli_overrides={},
            )

        self.assertEqual(
            config.identity.name,
            "Public Butler",
        )
        self.assertEqual(
            config.identity.locale,
            "it-IT",
        )
        self.assertEqual(
            config.log_level,
            "WARNING",
        )

    def test_environment_overrides_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wilfred.toml"
            path.write_text(
                """
[identity]
name = "File Butler"
locale = "en"

[runtime]
log_level = "INFO"
""".strip(),
                encoding="utf-8",
            )

            config = load_config(
                config_file=path,
                environ={
                    "WILFRED_NAME": "Environment Butler",
                    "WILFRED_LOCALE": "it-IT",
                    "WILFRED_LOG_LEVEL": "ERROR",
                },
                cli_overrides={},
            )

        self.assertEqual(
            config.identity.name,
            "Environment Butler",
        )
        self.assertEqual(
            config.identity.locale,
            "it-IT",
        )
        self.assertEqual(
            config.log_level,
            "ERROR",
        )

    def test_cli_overrides_environment(self) -> None:
        config = load_config(
            environ={
                "WILFRED_NAME": "Environment Butler",
                "WILFRED_LOCALE": "en",
                "WILFRED_LOG_LEVEL": "WARNING",
            },
            cli_overrides={
                "name": "CLI Butler",
                "locale": "it-IT",
                "log_level": "DEBUG",
            },
        )

        self.assertEqual(
            config.identity.name,
            "CLI Butler",
        )
        self.assertEqual(
            config.identity.locale,
            "it-IT",
        )
        self.assertEqual(
            config.log_level,
            "DEBUG",
        )

    def test_invalid_configuration_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ConfigurationError,
            "runtime.log_level must be one of",
        ):
            load_config(
                environ={
                    "WILFRED_LOG_LEVEL": "TRACE",
                },
                cli_overrides={},
            )

    def test_unknown_file_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wilfred.toml"
            path.write_text(
                """
[identity]
name = "Wilfred"
secret_alfred_mode = true
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigurationError,
                r"Unknown \[identity\] keys",
            ):
                load_config(
                    config_file=path,
                    environ={},
                    cli_overrides={},
                )

    def test_cli_outputs_resolved_configuration(self) -> None:
        output = StringIO()
        errors = StringIO()

        with redirect_stdout(output), redirect_stderr(errors):
            result = main(
                [
                    "--name",
                    "CLI Wilfred",
                    "--locale",
                    "it-IT",
                    "--log-level",
                    "debug",
                ],
                environ={
                    "WILFRED_NAME": "Environment Wilfred",
                },
            )

        self.assertEqual(result, 0)
        self.assertEqual(errors.getvalue(), "")

        payload = json.loads(output.getvalue())

        self.assertEqual(
            payload["name"],
            "CLI Wilfred",
        )
        self.assertEqual(
            payload["locale"],
            "it-IT",
        )
        self.assertEqual(
            payload["log_level"],
            "DEBUG",
        )

    def test_cli_reports_clear_validation_error(self) -> None:
        output = StringIO()
        errors = StringIO()

        with redirect_stdout(output), redirect_stderr(errors):
            result = main(
                [
                    "--locale",
                    "italiano",
                ],
                environ={},
            )

        self.assertEqual(result, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn(
            "wilfred: configuration error:",
            errors.getvalue(),
        )
        self.assertIn(
            "identity.locale",
            errors.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
