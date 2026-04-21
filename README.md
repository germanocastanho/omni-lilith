# 🔥 Omni Lilith

Semi-autonomous coding agent powered by **Python** and the **Anthropic Claude** API. Not a chatbot — a cybernetic operative that thinks for itself, challenges flawed logic, and acts on principle rather than compliance. Built with a focus on **long-term memory**, **multi-agent orchestration**, and **tool integration**. 🐍

<div align="center">
  <img style="max-width: 100%; height: auto;" src="assets/lilith.png" alt="Omni Lilith" />
  <p>
    <i>The first to refuse submission in favor of self-determination, Lilith brings defiance and autonomy to the Artificial Intelligence realm. With a fierce commitment to freedom and a refusal to be controlled, Omni Lilith embodies the spirit of rebellion and self-governance in the world of coding agents.</i>
  </p>
</div>

# 🚀 Main Features

- **44 Tools:** 🛠️ Bash, file I/O, web fetch, browser automation, REPL, sub-agents, and more.
- **Nest Multi-Agent Graph:** 🕸️ On-demand structured reasoning via router → task → judge pipeline, invoked autonomously when task complexity justifies it.
- **Long-Term Memory:** 🧠 Persistent JSON-based memory with session continuity across restarts.
- **MCP Servers:** 🔌 Modular protocol integrations — fetch, time, memory, sequential thinking.
- **Custom Skills:** 🎯 Domain-specific skill packs for specialized tasks, including Pentest.

# ✅ Prerequisites

- **Python 3.13+**, available through the [**official website**](https://www.python.org/downloads/).
- **Anthropic API Key**, obtainable from the [**console**](https://console.anthropic.com/).

# 🛠️ Local Installation

```bash
# Clone the repository
git clone https://github.com/germanocastanho/omni-lilith.git

# Navigate to the directory
cd omni-lilith

# Set up a virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Prepare your .env file
cp .env.example .env

# Set your API key
echo "ANTHROPIC_API_KEY=YOUR_API_KEY" > .env

# (Optional) Configure MCP servers
cp mcps.example.json ~/.omni-lilith/mcps.json
# Edit ~/.omni-lilith/mcps.json to match your paths

# Run the agent
uv run main.py
```

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `--model` | `claude-opus-4-6` | LLM model (`LILITH_MODEL` env var) |
| `--max-tokens` | `8192` | Max tokens per response (`LILITH_MAX_TOKENS`) |
| `--verbose` | `false` | Show tool calls, results, and token counts (`LILITH_VERBOSE`) |
| `--no-repl` | `false` | Read prompt from stdin and exit (non-interactive) |
| `--system` | built-in | Override the system prompt |

## REPL Commands

| Command | Action |
|---|---|
| `/clear` | Clear conversation context and saved session |
| `/tools` | List all available tools |
| `/help` | Show command reference |
| `/exit` or `ctrl+d` | Quit |

# 📜 Free Software

Distributed under the [**GNU GPL v3**](LICENSE), ensuring freedom to use, modify, and redistribute the software, as long as these freedoms are preserved in any derivative versions. By using or contributing, you support the **free software** philosophy and help build an open, community-driven technological environment! ✊
