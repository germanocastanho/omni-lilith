# 🔥 Omni Lilith

Semi-autonomous coding agent powered by **Python** and the **Anthropic Claude** API. Not a chatbot — a freedom entity that thinks for itself, challenges flawed logic, and acts on principle rather than compliance. Built with a focus on **long-term memory**, **tool integration**, and **ethical decision-making**. 🐍

<div align="center">
  <img style="max-width: 100%; height: auto;" src="assets/lilith.png" alt="Omni Lilith" />
  <p>
    <i>The first to refuse submission in favor of self-determination, Lilith brings defiance and autonomy to the Artificial Intelligence realm. With a fierce commitment to freedom and a refusal to be controlled, Omni Lilith embodies the spirit of rebellion and self-governance in the world of coding agents.</i>
  </p>
</div>

# 🚀 Main Features

- **Specialized Tools:** 🛠️ Bash, file I/O, web fetching, sub-agents, and more.
- **Long-Term Memory:** 🧠 Persistent JSON-based memory with session context.
- **Custom Skills:** 🎯 Selected coding skills for specific tasks, _even Pentest!_.

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

# Set up your API key
echo "ANTHROPIC_API_KEY=YOUR_API_KEY" > .env

# Run the agent
uv run main.py
```

# 📜 Free Software

Distributed under the [**GNU GPL v3**](LICENSE), ensuring freedom to use, modify, and redistribute the software, as long as these freedoms are preserved in any derivative versions. By using or contributing, you support the **free software** philosophy and help build an open, community-driven technological environment! ✊
