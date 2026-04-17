import pytest

from src.tools.glob_tool import _call


async def test_glob_finds_files(ctx, tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "b.py").write_text("x")
    result = await _call({"pattern": "*.py", "path": str(tmp_path)}, ctx)
    text = result.content[0]["text"]
    assert "a.py" in text
    assert "b.py" in text
    assert not result.is_error


async def test_glob_no_matches(ctx, tmp_path):
    result = await _call({"pattern": "*.ts", "path": str(tmp_path)}, ctx)
    assert result.content[0]["text"] == "(no matches)"
    assert not result.is_error


async def test_glob_missing_dir(ctx, tmp_path):
    result = await _call({"pattern": "*.py", "path": str(tmp_path / "ghost")}, ctx)
    assert result.is_error
    assert "not found" in result.content[0]["text"]


async def test_glob_truncates_at_1000(ctx, tmp_path):
    for i in range(1010):
        (tmp_path / f"f{i}.txt").write_text("")
    result = await _call({"pattern": "*.txt", "path": str(tmp_path)}, ctx)
    assert "omitted" in result.content[0]["text"]
    assert not result.is_error


async def test_glob_recursive_pattern(ctx, tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "deep.py").write_text("")
    result = await _call({"pattern": "**/*.py", "path": str(tmp_path)}, ctx)
    assert "deep.py" in result.content[0]["text"]
