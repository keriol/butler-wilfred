from __future__ import annotations

from importlib.metadata import version

import unittest

from wilfred import __version__
from wilfred.__main__ import runtime_status


class WilfredBootstrapTests(unittest.TestCase):
    def test_package_version(self) -> None:
        self.assertEqual(__version__, version("wilfred-butler"))

    def test_standalone_runtime_status(self) -> None:
        status = runtime_status()

        self.assertEqual(status["name"], "Wilfred")
        self.assertEqual(status["status"], "ok")
        self.assertEqual(
            status["runtime"],
            "standalone-bootstrap",
        )


if __name__ == "__main__":
    unittest.main()
