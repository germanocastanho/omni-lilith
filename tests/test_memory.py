from unittest.mock import patch

import nest.memory as mem_mod
from nest.memory import (
    append_note,
    dump_all,
    get_memory_prompt,
    read_memory,
    write_memory,
)


def _patch_path(tmp_path):
    return patch.object(mem_mod, "_MEMORY_PATH", tmp_path / "ltm.json")


def test_read_missing_key_returns_empty(tmp_path):
    with _patch_path(tmp_path):
        assert read_memory("nonexistent") == ""


def test_write_and_read_fact(tmp_path):
    with _patch_path(tmp_path):
        write_memory("facts", "name", "Lilith")
        assert read_memory("name") == "Lilith"


def test_write_and_read_preference(tmp_path):
    with _patch_path(tmp_path):
        write_memory("preferences", "lang", "pt-BR")
        assert read_memory("lang") == "pt-BR"


def test_write_and_read_user_context(tmp_path):
    with _patch_path(tmp_path):
        write_memory("user_context", "role", "operator")
        assert read_memory("role") == "operator"


def test_invalid_section_defaults_to_facts(tmp_path):
    with _patch_path(tmp_path):
        write_memory("bogus_section", "key", "val")
        assert read_memory("key") == "val"


def test_write_overwrites_existing_key(tmp_path):
    with _patch_path(tmp_path):
        write_memory("facts", "x", "first")
        write_memory("facts", "x", "second")
        assert read_memory("x") == "second"


def test_append_note(tmp_path):
    with _patch_path(tmp_path):
        append_note("session started")
        data = dump_all()
    assert "session started" in data["session_notes"]


def test_append_multiple_notes(tmp_path):
    with _patch_path(tmp_path):
        for i in range(5):
            append_note(f"note {i}")
        data = dump_all()
    assert len(data["session_notes"]) == 5
    assert data["session_notes"][0] == "note 0"


def test_notes_truncated_at_100(tmp_path):
    with _patch_path(tmp_path):
        for i in range(110):
            append_note(f"n{i}")
        data = dump_all()
    assert len(data["session_notes"]) == 100
    assert data["session_notes"][0] == "n10"


def test_get_memory_prompt_empty(tmp_path):
    with _patch_path(tmp_path):
        result = get_memory_prompt()
    assert result == ""


def test_get_memory_prompt_with_facts(tmp_path):
    with _patch_path(tmp_path):
        write_memory("facts", "color", "black")
        result = get_memory_prompt()
    assert "<long_term_memory>" in result
    assert "color" in result
    assert "black" in result


def test_get_memory_prompt_with_preferences(tmp_path):
    with _patch_path(tmp_path):
        write_memory("preferences", "theme", "dark")
        result = get_memory_prompt()
    assert "theme" in result
    assert "dark" in result


def test_get_memory_prompt_with_notes(tmp_path):
    with _patch_path(tmp_path):
        append_note("remembered this")
        result = get_memory_prompt()
    assert "remembered this" in result


def test_get_memory_prompt_notes_shows_last_5(tmp_path):
    with _patch_path(tmp_path):
        for i in range(10):
            append_note(f"note {i}")
        result = get_memory_prompt()
    assert "note 9" in result
    assert "note 4" not in result


def test_dump_all_returns_full_structure(tmp_path):
    with _patch_path(tmp_path):
        write_memory("facts", "k", "v")
        append_note("test")
        data = dump_all()
    assert "facts" in data
    assert "preferences" in data
    assert "session_notes" in data
    assert "user_context" in data


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "ltm.json"
    path.write_text("not json")
    with _patch_path(tmp_path):
        data = dump_all()
    assert data == mem_mod._EMPTY


def test_atomic_write_uses_tmp_file(tmp_path):
    with _patch_path(tmp_path):
        write_memory("facts", "k", "v")
    assert (tmp_path / "ltm.json").exists()
    assert not (tmp_path / "ltm.json.tmp").exists()
