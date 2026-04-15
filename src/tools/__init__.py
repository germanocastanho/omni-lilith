from src.tool import Tool
from src.tools.agent_tool import TOOL as AgentTool
from src.tools.ask_user_tool import TOOL as AskUserQuestionTool
from src.tools.bash_tool import TOOL as BashTool
from src.tools.browser_tool import TOOL as BrowserTool
from src.tools.brief_tool import TOOL as BriefTool
from src.tools.config_tool import TOOL as ConfigTool
from src.tools.file_edit_tool import TOOL as EditTool
from src.tools.file_read_tool import TOOL as ReadTool
from src.tools.file_write_tool import TOOL as WriteTool
from src.tools.glob_tool import TOOL as GlobTool
from src.tools.grep_tool import TOOL as GrepTool
from src.tools.lsp_tool import TOOL as LSPTool
from src.tools.mcp_auth_tool import TOOL as McpAuthTool
from src.tools.mcp_resource_tools import LIST_MCP_RESOURCES, READ_MCP_RESOURCE
from src.tools.mcp_tool import TOOL as MCPTool
from src.tools.notebook_edit_tool import TOOL as NotebookEditTool
from src.tools.plan_mode_tools import ENTER_PLAN_MODE, EXIT_PLAN_MODE
from src.tools.powershell_tool import TOOL as PowerShellTool
from src.tools.remote_trigger_tool import TOOL as RemoteTriggerTool
from src.tools.repl_tool import TOOL as REPLTool
from src.tools.schedule_cron_tool import CRON_CREATE, CRON_DELETE, CRON_LIST
from src.tools.send_message_tool import TOOL as SendMessageTool
from src.tools.skill_tool import TOOL as SkillTool
from src.tools.sleep_tool import TOOL as SleepTool
from src.tools.synthetic_output_tool import TOOL as SyntheticOutputTool
from src.tools.task_tools import (
    TASK_CREATE,
    TASK_GET,
    TASK_LIST,
    TASK_OUTPUT,
    TASK_STOP,
    TASK_UPDATE,
)
from src.tools.team_tools import TEAM_CREATE, TEAM_DELETE
from src.tools.todo_write_tool import TOOL as TodoWriteTool
from src.tools.tool_search_tool import TOOL as ToolSearchTool
from src.tools.web_fetch_tool import TOOL as WebFetchTool
from src.tools.web_search_tool import TOOL as WebSearchTool
from src.tools.worktree_tools import ENTER_WORKTREE, EXIT_WORKTREE

ALL_TOOLS: list[Tool] = [
    # Core I/O
    BashTool,
    BrowserTool,
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    PowerShellTool,
    # Network
    WebFetchTool,
    WebSearchTool,
    # Agent & Tasks
    AgentTool,
    TASK_CREATE,
    TASK_LIST,
    TASK_GET,
    TASK_UPDATE,
    TASK_STOP,
    TASK_OUTPUT,
    SendMessageTool,
    # Interactive
    AskUserQuestionTool,
    ENTER_PLAN_MODE,
    EXIT_PLAN_MODE,
    ENTER_WORKTREE,
    EXIT_WORKTREE,
    REPLTool,
    # Utilities
    NotebookEditTool,
    SleepTool,
    TodoWriteTool,
    ToolSearchTool,
    CRON_CREATE,
    CRON_DELETE,
    CRON_LIST,
    RemoteTriggerTool,
    BriefTool,
    ConfigTool,
    SkillTool,
    SyntheticOutputTool,
    TEAM_CREATE,
    TEAM_DELETE,
    # MCP & LSP
    MCPTool,
    McpAuthTool,
    LIST_MCP_RESOURCES,
    READ_MCP_RESOURCE,
    LSPTool,
]

__all__ = ["ALL_TOOLS"]
