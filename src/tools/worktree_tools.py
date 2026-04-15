
from src.tool import Tool, ToolResult, build_tool
from src.utils.shell import exec_cmd

_ENTER_SCHEMA = {
    "type": "object",
    "properties": {
        "branch": {
            "type": "string",
            "description": "Branch name for the worktree.",
        },
        "path": {
            "type": "string",
            "description": "Path where the worktree should be created.",
        },
    },
    "required": ["branch"],
}

_EXIT_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Path of the worktree to remove.",
        },
    },
    "required": ["path"],
}


async def _enter(args: dict, ctx) -> ToolResult:
    branch = args["branch"]
    path = args.get("path", f"/tmp/worktree-{branch}")
    result = await exec_cmd(
        f"git worktree add {path} {branch}", timeout=30
    )
    if result.exit_code != 0:
        result2 = await exec_cmd(
            f"git worktree add -b {branch} {path}", timeout=30
        )
        if result2.exit_code != 0:
            return ToolResult(
                content=[
                    {"type": "text", "text": result2.stderr}
                ],
                is_error=True,
            )
        path_info = path
    else:
        path_info = path

    return ToolResult(
        content=[
            {
                "type": "text",
                "text": f"Worktree created at {path_info} (branch: {branch})",
            }
        ]
    )


async def _exit(args: dict, ctx) -> ToolResult:
    path = args["path"]
    result = await exec_cmd(
        f"git worktree remove --force {path}", timeout=30
    )
    if result.exit_code != 0:
        return ToolResult(
            content=[{"type": "text", "text": result.stderr}],
            is_error=True,
        )
    return ToolResult(
        content=[
            {"type": "text", "text": f"Worktree at {path} removed."}
        ]
    )


ENTER_WORKTREE = build_tool(
    Tool(
        name="EnterWorktree",
        description="Create a git worktree for isolated branch work.",
        input_schema=_ENTER_SCHEMA,
        call=_enter,
        search_hint="git worktree branch isolated copy",
    )
)

EXIT_WORKTREE = build_tool(
    Tool(
        name="ExitWorktree",
        description="Remove a git worktree.",
        input_schema=_EXIT_SCHEMA,
        call=_exit,
        search_hint="git worktree remove delete cleanup",
    )
)
