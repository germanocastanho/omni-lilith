def truncate(text: str, max_chars: int = 100_000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    omitted = len(text) - max_chars
    return (
        text[:half]
        + f"\n\n... [{omitted} chars omitted] ...\n\n"
        + text[-half:]
    )


def truncate_lines(text: str, max_lines: int = 2000) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    omitted = len(lines) - max_lines
    half = max_lines // 2
    kept = lines[:half] + [f"... [{omitted} lines omitted] ..."] + lines[-half:]
    return "\n".join(kept)
