from __future__ import annotations

from pathlib import Path
import unittest

from wilfred import (
    OutputAdapter,
    OutputCapability,
    OutputDeliveryResult,
    OutputDeliveryStatus,
    OutputKind,
    OutputPriority,
    OutputRequest,
)


class FakeSpeechAdapter:
    @property
    def name(self) -> str:
        return "fake-speech"

    def capabilities(
        self,
    ) -> frozenset[OutputCapability]:
        return frozenset({OutputCapability.SPEECH})

    def deliver(
        self,
        request: OutputRequest,
    ) -> OutputDeliveryResult:
        supported = (
            request.required_capability
            in self.capabilities()
        )

        return OutputDeliveryResult(
            request_id=request.request_id,
            adapter_name=self.name,
            status=(
                OutputDeliveryStatus.DELIVERED
                if supported
                else OutputDeliveryStatus.UNSUPPORTED
            ),
            error_code=(
                None
                if supported
                else "unsupported_capability"
            ),
        )


class OutputContractTests(unittest.TestCase):
    def test_request_defaults(self) -> None:
        request = OutputRequest(
            content="Laundry completed.",
            kind=OutputKind.SPEECH,
            target="kitchen",
        )

        self.assertTrue(request.request_id)
        self.assertEqual(
            request.priority,
            OutputPriority.NORMAL,
        )
        self.assertEqual(
            request.required_capability,
            OutputCapability.SPEECH,
        )

    def test_adapter_protocol(self) -> None:
        self.assertIsInstance(
            FakeSpeechAdapter(),
            OutputAdapter,
        )

    def test_supported_delivery(self) -> None:
        request = OutputRequest(
            content="Laundry completed.",
            kind=OutputKind.SPEECH,
        )
        result = FakeSpeechAdapter().deliver(request)

        self.assertTrue(result.ok)
        self.assertEqual(
            result.status,
            OutputDeliveryStatus.DELIVERED,
        )

    def test_unsupported_delivery(self) -> None:
        request = OutputRequest(
            content="Show status.",
            kind=OutputKind.DISPLAY,
        )
        result = FakeSpeechAdapter().deliver(request)

        self.assertFalse(result.ok)
        self.assertEqual(
            result.status,
            OutputDeliveryStatus.UNSUPPORTED,
        )
        self.assertEqual(
            result.error_code,
            "unsupported_capability",
        )

    def test_failed_delivery_is_not_ok(self) -> None:
        result = OutputDeliveryResult(
            request_id="request-1",
            adapter_name="fake",
            status=OutputDeliveryStatus.FAILED,
        )

        self.assertFalse(result.ok)

    def test_contract_is_provider_agnostic(self) -> None:
        module = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "wilfred"
            / "output.py"
        )
        text = module.read_text(encoding="utf-8").lower()

        for provider in (
            "alexa",
            "google home",
            "home assistant",
            "echo",
            "keriol",
        ):
            self.assertNotIn(provider, text)


if __name__ == "__main__":
    unittest.main()
