
# 🧠 Talos: YAML-First LLM DAG Orchestrator

Talos is a lightweight, YAML-first DAG orchestration framework for running LLM agent workflows — inspired by Airflow, but optimized for modern LLM-native automation with minimal infra overhead.

---

## 📦 Install

[![Talos CLI](https://img.shields.io/badge/pip-install%20talos-blue?logo=pypi)](https://github.com/abhijnanacharya/talos_cli/releases/latest)

> Download the latest `.whl` or `.tar.gz` from [GitHub Releases](https://github.com/abhijnanacharya/talos_cli/releases/latest) and run:

```bash
pip install llm_orchestrator-0.1.0-py3-none-any.whl
```

---

## 🚀 Features

- ✅ YAML-based DAG definition (`config/*.yaml`)
- ✅ Agent abstraction layer for tasks like summarization, extraction, etc.
- ✅ Pluggable architecture: add custom agents via `orchestrator/agents`
- ✅ CLI interface to run DAGs like Docker/K8s:
  ```bash
  talos run -f config/test.yaml
  ```
- ✅ Dependency-respecting step execution
- ✅ Run any DAG using the `talos` command installed globally

---

## 📦 Project Structure

```
LLM_ORCHESTRATOR/
├── cli/                   # CLI entrypoint with Typer + Rich
│   └── main.py            # Registered via pyproject.toml:
│                          # [project.scripts]
│                          # talos = "cli.main:run_cli"
├── config/                # DAG & agent configuration
│   ├── test.yaml
│   └── agents.yaml
├── data/                  # Inputs for agents (emails, etc.)
│   └── email_client/
│       ├── fetcher.py
│       └── task_extractor.py
├── orchestrator/
│   ├── dag_executor.py    # DAG parsing & step execution
│   └── agents/            # Custom agents live here
│       ├── helloWorld.py
│       ├── summarizer.py
│       ├── gmail_reader.py
│       ├── gpt_task_extractor.py
│       └── discord_notifier.py
├── utils/                 # Utility functions (TBD)
├── pyproject.toml         # Project metadata (includes CLI entry)
├── .lock                  # uv lock file for dependencies
├── Dockerfile             # uv-based container build
└── docker-compose.yaml    # Easy container execution
```

---

## 🛠️ Running the Project

### 1. 🐳 Using Docker

```bash
docker-compose build
docker-compose up
```

### 2. 🧪 Local Dev (CLI-based)

```bash
# Install globally in dev mode
pip install -e .

# Run a DAG
talos run -f config/test.yaml

# List previously run DAGs
talos list

# Show version
talos --version

# Show help with logo and panel
talos --help
```

---

## ✍️ Authoring a DAG

Create a YAML file under `config/`:

```yaml
name: test_sample_dag
steps:
  - id: test_step
    agent: helloWorld
    depends_on: []
```

You can register agents in `config/agents.yaml`.

---

## 🧩 Agents

Each agent must implement a `run()` method and register under `config/agents.yaml`. Sample agents:

- `helloWorld`: Basic test agent
- `summarizer`: Summarizes input from emails or text
- `gmail_reader`: Reads latest emails from Gmail
- `gpt_task_extractor`: Extracts action items using GPT
- `discord_notifier`: Sends summarized updates to Discord

---

## 🧱 TODOs / Roadmap

- [ ] Add agent registry class
- [ ] Add error handling, retries
- [ ] Parallel execution (where `depends_on` permits)
- [ ] Scheduling (cron-style)
- [ ] Logs and visual DAG UI
- [ ] DAG validation before execution
- [ ] Parameter injection via environment or CLI

---

## 📄 Example DAG: `daily_p0_digest.yaml`

```yaml
name: daily_p0_digest

steps:
  - id: fetch_emails
    agent: gmail_reader
    params:
      label: "INBOX"
    output: emails
    depends_on: []

  - id: extract_p0
    agent: gpt_task_extractor
    input: ${fetch_emails.output}
    depends_on: [fetch_emails]

  - id: summarize
    agent: gpt_summarizer
    input: ${extract_p0.output}
    depends_on: [extract_p0]

  - id: notify_user
    agent: discord_notifier
    input: ${summarize.output}
    depends_on: [summarize]
```

---

### 📸 Example: Daily P0 Digest Flow

This DAG runs a complete P0 triage workflow:

1. ✅ Reads emails from Gmail inbox (`gmail_reader`)
2. ✅ Extracts critical tasks using GPT (`gpt_task_extractor`)
3. ✅ Summarizes tasks with another GPT call (`gpt_summarizer`)
4. ✅ Sends the result to a Discord channel (`discord_notifier`)

📷 _Screenshot_:

![Talos_cli_example](https://github.com/user-attachments/assets/8e2691df-ed2e-405f-b622-56149a02f18c)

---

## 🧑‍💻 Maintainer

Built by Abhijnan Acharya, inspired by frustration with tangled LLM prompt chains and LangChain fatigue.

---

## 📄 License

MIT License.
