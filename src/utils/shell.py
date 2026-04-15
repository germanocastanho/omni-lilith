import asyncio
from dataclasses import dataclass


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int


async def exec_cmd(
    command: str,
    timeout: float = 120.0,
    cwd: str | None = None,
) -> ExecResult:
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return ExecResult(
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            exit_code=124,
        )

    return ExecResult(
        stdout=stdout_b.decode(errors="replace"),
        stderr=stderr_b.decode(errors="replace"),
        exit_code=proc.returncode or 0,
    )
