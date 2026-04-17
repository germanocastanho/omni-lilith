import json
from pathlib import Path
from unittest.mock import patch

import pytest

import src.tools.config_tool as config_mod
from src.tools.config_tool import _call


async def test_read_missing_key(ctx, tmp_path):
    config_path = tmp_path / "config.json"
    with patch.object(config_mod, "_CONFIG_PATH", config_path):
        result = await _call({"key": "nonexistent"}, ctx)
    assert "not set" in result.content[0]["text"]
    assert not result.is_error


async def test_write_then_read(ctx, tmp_path):
    config_path = tmp_path / "config.json"
    with patch.object(config_mod, "_CONFIG_PATH", config_path):
        write_result = await _call({"key": "theme", "value": "dark"}, ctx)
        assert "updated" in write_result.content[0]["text"]

        read_result = await _call({"key": "theme"}, ctx)
    assert json.loads(read_result.content[0]["text"]) == "dark"


async def test_overwrite_key(ctx, tmp_path):
    config_path = tmp_path / "config.json"
    with patch.object(config_mod, "_CONFIG_PATH", config_path):
        await _call({"key": "x", "value": 1}, ctx)
        await _call({"key": "x", "value": 2}, ctx)
        result = await _call({"key": "x"}, ctx)
    assert json.loads(result.content[0]["text"]) == 2


async def test_config_creates_parent_dir(ctx, tmp_path):
    config_path = tmp_path / "nested" / "dir" / "config.json"
    with patch.object(config_mod, "_CONFIG_PATH", config_path):
        await _call({"key": "k", "value": "v"}, ctx)
    assert config_path.exists()


async def test_config_corrupt_file_returns_empty(ctx, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("NOT JSON", encoding="utf-8")
    with patch.object(config_mod, "_CONFIG_PATH", config_path):
        result = await _call({"key": "anything"}, ctx)
    assert "not set" in result.content[0]["text"]
