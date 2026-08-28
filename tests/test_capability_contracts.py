from __future__ import annotations

import unittest

from wilfred import (
    CapabilityDefinition,
    DomainDefinition,
)


class CapabilityContractTests(unittest.TestCase):
    def test_domain_has_stable_public_identity(self) -> None:
        domain = DomainDefinition(
            name="media",
            description="Media discovery and playback.",
        )

        self.assertEqual(domain.identity, "media")
        self.assertEqual(domain.name, "media")
        self.assertEqual(
            domain.description,
            "Media discovery and playback.",
        )

    def test_capability_identity_is_domain_qualified(self) -> None:
        capability = CapabilityDefinition(
            name="playback",
            domain="media",
            description="Play resolved media.",
        )

        self.assertEqual(capability.identity, "media.playback")
        self.assertEqual(capability.domain, "media")

    def test_contracts_are_immutable(self) -> None:
        domain = DomainDefinition(name="media")
        capability = CapabilityDefinition(
            name="playback",
            domain="media",
        )

        with self.assertRaises(AttributeError):
            domain.name = "other"  # type: ignore[misc]

        with self.assertRaises(AttributeError):
            capability.name = "other"  # type: ignore[misc]

    def test_invalid_domain_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Invalid domain name",
        ):
            DomainDefinition(name="Media Domain")

    def test_invalid_capability_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Invalid capability name",
        ):
            CapabilityDefinition(
                name="Play Media",
                domain="media",
            )

    def test_invalid_capability_domain_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Invalid domain name",
        ):
            CapabilityDefinition(
                name="playback",
                domain="Media Domain",
            )

    def test_equivalent_definitions_compare_deterministically(self) -> None:
        left = CapabilityDefinition(
            name="playback",
            domain="media",
            description="Play resolved media.",
        )
        right = CapabilityDefinition(
            name="playback",
            domain="media",
            description="Play resolved media.",
        )

        self.assertEqual(left, right)
        self.assertEqual(hash(left), hash(right))


if __name__ == "__main__":
    unittest.main()
