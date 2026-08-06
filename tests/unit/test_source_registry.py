"""Unit tests for SourceRegistry (no DB, no network)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from signal_bot.domain.enums import ConflictPolicy
from signal_bot.sources import SourceConfig, SourceRegistry, build_example_registry


def test_source_config_frozen():
    src = SourceConfig(
        source_id="src1",
        name="Alpha",
        parser_id="generic_structured",
        account_id="acc1",
        profile_id="p1",
    )
    assert src.enabled is True
    assert src.conflict_policy == ConflictPolicy.REJECT_SECOND
    with pytest.raises(ValidationError):
        src.enabled = False  # type: ignore[misc]


def test_registry_register_and_get():
    reg = SourceRegistry()
    src = SourceConfig(
        source_id="src_a",
        name="A",
        parser_id="generic_structured",
        account_id="acc",
        profile_id="prof",
    )
    reg.register(src)
    assert reg.get("src_a") is src
    assert reg.get("missing") is None


def test_registry_enabled_filter():
    reg = SourceRegistry()
    reg.register(
        SourceConfig(
            source_id="on",
            name="On",
            parser_id="generic_structured",
            account_id="a",
            profile_id="p",
            enabled=True,
        )
    )
    reg.register(
        SourceConfig(
            source_id="off",
            name="Off",
            parser_id="generic_structured",
            account_id="a",
            profile_id="p",
            enabled=False,
        )
    )
    assert reg.get_enabled("on") is not None
    assert reg.get_enabled("off") is None
    assert len(reg.list_enabled()) == 1
    assert len(reg.list_all()) == 2


def test_disable_enable():
    reg = SourceRegistry()
    reg.register(
        SourceConfig(
            source_id="s1",
            name="S",
            parser_id="generic_structured",
            account_id="a",
            profile_id="p",
        )
    )
    assert reg.disable("s1") is True
    assert reg.get("s1") is not None
    assert reg.get("s1").enabled is False  # type: ignore[union-attr]
    assert reg.enable("s1") is True
    assert reg.get("s1").enabled is True  # type: ignore[union-attr]
    assert reg.disable("missing") is False


def test_example_registry():
    reg = build_example_registry()
    assert len(reg.list_enabled()) >= 1
    demo = reg.get("src_demo_alpha")
    assert demo is not None
    assert demo.parser_id == "generic_structured"
    assert demo.telegram_chat_id is None  # no live Telegram in Phase 2
