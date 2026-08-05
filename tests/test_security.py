from __future__ import annotations

from scripts.security_check import SECRET_PATTERNS


def test_authorization_key_pattern_is_detected() -> None:
    fake_key = "AQ." + "x" * 40
    assert any(pattern.search(fake_key) for pattern in SECRET_PATTERNS)
