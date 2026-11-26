# General-Purpose Research & Planning Agent (LangGraph)

A runnable starter project implementing the supplied problem statement: a domain-independent multi-step agent that plans research, runs independent searches in parallel, synthesizes a cited report and action plan, critiques its own draft, and can pause for human approval. LangGraph provides graph orchestration and an interrupt/checkpointer workflow.

## 1. Requirements

- Windows 10/11 (scripts included), macOS, or Linux
- Python **3.11 or 3.12** (recommended)
- Internet connection for installing packages and web search
- VS Code (recommended) with the Microsoft Python extension
- Optional: an LLM provider key or a local Ollama installation. The project starts in `mock` mode without an LLM key so you can verify the UI and workflow first.

## 2. Windows quick start

1. Extract the ZIP to a normal writable folder (not inside a ZIP preview).
2. Open the folder in VS Code: **File → Open Folder**.
3. Double-click `setup.bat`. It creates `.venv`, installs packages, and creates `.env` from `.env.example`.
4. Double-click `run.bat`. The Streamlit app opens in your browser (normally `http://localhost:8501`).
5. Enter a research question and click **Start research**.

If Windows blocks the scripts, open Command Prompt in the project folder and run `setup.bat`, then `run.bat`.

## 3. VS Code terminal commands

```powershell
# Create environment (choose the Python version installed on your machine)
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python -m streamlit run app/main.py
```

Run the command-line version:

```powershell
.venv\Scripts\activate
python run_cli.py "Compare three approaches to learning cloud security and create a 10-week roadmap"
```

Run tests:

```powershell
.venv\Scripts\activate
python -m pytest -q
```

## 4. Configure an LLM (optional but recommended)

Edit `.env` (never share or commit this file). Set `LLM_PROVIDER` and `LLM_MODEL`:

| Provider | `.env` example | Credential / prerequisite |
|---|---|---|
| Built-in mock | `LLM_PROVIDER=mock` | No key; setup/demo mode, not high-quality research synthesis |
| Ollama local | `LLM_PROVIDER=ollama` and `LLM_MODEL=llama3.1` | Install Ollama, start it, then `ollama pull llama3.1` |
| OpenAI | `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini` | Set `OPENAI_API_KEY` |
| Anthropic | `LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-3-5-haiku-latest` | Set `ANTHROPIC_API_KEY` |
| Google | `LLM_PROVIDER=google_genai`, `LLM_MODEL=gemini-2.0-flash` | Set `GOOGLE_API_KEY` |

Only the selected provider's credential is needed. Provider/model availability and pricing can change; check the provider's current model documentation. If you use Ollama, ensure the Ollama server is running before starting the app.

## 5. Configure web search

- `SEARCH_PROVIDER=auto`: Tavily when `TAVILY_API_KEY` is present, otherwise DuckDuckGo.
- `SEARCH_PROVIDER=duckduckgo`: no API key required; depends on the public DuckDuckGo search service and may be rate-limited or unavailable at times.
- `SEARCH_PROVIDER=tavily`: set `TAVILY_API_KEY` for a dedicated search API.

Tavily is the alternative if DuckDuckGo is throttled. DuckDuckGo is the no-key alternative if you do not want a search API key. Search availability depends on the external service and network; the app reports per-step search errors rather than pretending it found sources.

## 6. Main settings

```dotenv
MAX_REFLECTION_LOOPS=2
MAX_RESEARCH_STEPS=5
REQUIRE_HUMAN_APPROVAL=false
```

Set `REQUIRE_HUMAN_APPROVAL=true` to show the proposed plan and wait for approval before searching. You can also toggle approval in the UI. Reflection loops are capped to prevent endless retries.

## 7. Project structure

```text
research_planning_agent/
├── app/
│   ├── config.py       # Environment settings
│   ├── graph.py        # LangGraph StateGraph, Send fan-out, interrupt, critique loop
│   ├── llm.py          # Mock/Ollama/OpenAI/Anthropic/Google adapter
│   ├── main.py         # Streamlit user interface
│   ├── reporting.py    # Markdown report export
│   └── search.py       # Tavily / DuckDuckGo search adapters
├── tests/              # Small parser tests
├── output/             # Generated Markdown reports
├── .env.example
├── requirements.txt
├── setup.bat           # Windows one-time installation
├── run.bat             # Launch web UI
├── run_cli.bat         # Launch CLI
├── run_cli.py
└── README.md
```

## 8. Workflow

1. **Plan:** LLM creates a small list of independent search tasks.
2. **Human approval (optional):** LangGraph `interrupt()` pauses before research; the UI resumes with `Command(resume=True)` or cancels. Checkpoints are stored in SQLite.
3. **Parallel research:** LangGraph `Send` fans out tasks to independent search workers.
4. **Synthesis:** LLM creates a structured report and action plan from retrieved evidence.
5. **Critique:** LLM checks for important evidence gaps.
6. **Reflection:** If gaps are found, follow-up searches run, up to `MAX_REFLECTION_LOOPS`.
7. **Export:** Download or save the report as Markdown under `output/`.

## 9. Troubleshooting

- **`py` is not recognized:** install Python 3.11/3.12 and enable the Python Launcher and PATH options.
- **`ModuleNotFoundError`:** activate `.venv` and run `python -m pip install -r requirements.txt` again.
- **PowerShell activation policy:** you can avoid activation and call `.venv\Scripts\python.exe` directly, as the batch scripts do.
- **Search returns no results:** check internet access; try `SEARCH_PROVIDER=tavily` with a key, or switch back to `duckduckgo`.
- **Provider authentication error:** check `.env`, key spelling, provider selection, and whether the key has billing/access enabled. Restart Streamlit after editing `.env`.
- **Ollama connection error:** start Ollama and verify `http://localhost:11434` is reachable; pull the model named in `LLM_MODEL`.
- **Port 8501 is busy:** run `python -m streamlit run app/main.py --server.port 8502`.

## 10. Important reliability and safety notes

This is a complete runnable starter implementation, not a guarantee that external APIs will never fail. Web search can be rate-limited, LLMs can return malformed output, and sources can be inaccurate or change. The planner has a fallback plan if JSON parsing fails; failed search tasks are shown in the findings. Always open and verify important source links before relying on a report, especially for legal, medical, financial, or safety decisions. Mock mode verifies the software path but does not provide real LLM-quality reasoning.

## 11. Extending the project

- Add another search provider in `app/search.py`.
- Add another LLM adapter in `app/llm.py`.
- The app uses a local SQLite checkpointer (`checkpoints.sqlite`) so interrupted sessions can be resumed across app reruns and process restarts when the same thread ID is reused. Streamlit creates a fresh thread per browser session. For multi-user production deployment, use a managed Postgres checkpointer and authentication.
- Add domain-specific output schemas or document export formats as needed.
