<div align="center">

# 🤖 Sales Intelligence Chat — Ask Your Data Anything

### *No SQL. No pivot tables. Just plain English.*

Chat with a **14-million-row sales dataset** in real time using GPT-4 and LangChain agents.  
Ask follow-up questions, get instant breakdowns, and export results — all in a sleek dark dashboard.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-green?logo=chainlink&logoColor=white)](https://langchain.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1-412991?logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

![Sales Intelligence Chat Demo](assets/demo-preview.png)

</div>

---

## ✨ What Makes This Special?

Most BI tools make you learn them. **Sales Intelligence Chat learns to talk to you.**

```
You  →  "Which region had the highest primary sales in Q1?"
AI   →  Region "North" leads Q1 with ₨ 48.3 M in primary sales,
        followed by "South" at ₨ 41.7 M.

You  →  "Break it down by brand."
AI   →  [renders a live sortable table]

You  →  "Which brand had the worst stockout rate in that region?"
AI   →  Brand "X" had the highest stockout rate at 34% in North during Q1.
```

The agent **remembers your entire session** — every follow-up question builds on the last answer, just like talking to a human analyst.

---

## 🚀 Features at a Glance

| Feature | What it does |
|---|---|
| 💬 **Natural-language queries** | Ask anything in plain English — no SQL, no formulas |
| 🧠 **Conversation memory** | Full context across follow-up questions in the same session |
| 📊 **Smart result rendering** | Auto-detects tables, numbers, and text for best display |
| 🗂️ **Full-dataset operation** | Runs across all 14 M rows — zero sampling, zero compromises |
| ⚡ **Memory-optimised loader** | Categorical dtypes + float32 downcast cuts RAM usage by ~60% |
| 🤖 **Live model switcher** | Swap between GPT-4.1, GPT-4o, GPT-3.5-turbo without restarting |
| 🔄 **Auto-rebuild on model change** | Engine and memory reset automatically when you switch models |
| 📥 **Auto-load dataset** | Drops the first supported file in `data/` at startup |
| ⬇️ **Export chat history** | Download your full conversation as JSON |
| 🎨 **Custom dark theme** | Industrial data-dashboard aesthetic with DM Mono + DM Sans |

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | [Streamlit](https://streamlit.io) |
| **AI Agent** | [LangChain](https://langchain.com) — `create_pandas_dataframe_agent` |
| **LLM** | [OpenAI GPT-4.1 / GPT-4o](https://openai.com) (configurable) |
| **Memory** | LangChain `ConversationBufferMemory` |
| **Data engine** | [pandas](https://pandas.pydata.org) with categorical + float32 optimisation |
| **Configuration** | Python `dataclass` (frozen) + `python-dotenv` |
| **Styling** | Custom CSS — dark dashboard theme |

---

## 📁 Project Structure

```
sales-chat-ai/
│
├── app.py                  # Entry point — Streamlit page config + layout
├── .env                    # OPENAI_API_KEY ← never commit this
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
│
├── data/
│   └── your_dataset.gz    # Your sales dataset (git-ignored)
│
├── app/
│   ├── config.py           # AppConfig frozen dataclass — all settings in one place
│   ├── data_loader.py      # Loads .gz / .csv / .xlsx / .parquet with memory tricks
│   ├── query_engine.py     # ★ LangChain Agent + ConversationBufferMemory
│   ├── chat_history.py     # Session-scoped UI history via st.session_state
│   └── ui.py               # All Streamlit rendering logic
│
└── assets/
    └── style.css           # Custom dark theme injected via st.markdown
```

---

## ⚙️ Quick Start

### 1. Clone

```bash
git clone https://github.com/your-username/sales-chat-ai.git
cd sales-chat-ai
```

### 2. Set up virtual environment

```bash
# macOS / Linux
python3.12 -m venv .venv && source .venv/bin/activate

# Windows
python -m venv .venv && .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verify:
```bash
python -c "import langchain, streamlit, pandas; print('All good ✅')"
```

### 4. Add your API key

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Get your key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). This file is already in `.gitignore`.

### 5. Add your dataset

Place your file in the `data/` folder. Supported formats:

| Format | Notes |
|---|---|
| `.gz` (gzipped CSV) | Primary — best for large files |
| `.csv` | Plain CSV |
| `.xlsx` / `.xls` | Excel workbooks |
| `.parquet` | Fastest for repeated loads |

The app auto-loads the first supported file it finds. If `data/` is empty, a file upload widget appears in the sidebar.

### 6. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) and start asking questions.

---

## 📋 Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.12+ | `python --version` |
| pip | 23+ | `pip --version` |
| OpenAI API key | — | [platform.openai.com](https://platform.openai.com/api-keys) |

---

## 🗄️ Dataset Schema (24 columns)

| Column | Type | Description |
|---|---|---|
| `month` | category | Calendar month name |
| `year` | int16 | Calendar / fiscal year |
| `region` | category | Top-level sales region |
| `city` | category | City |
| `area` | category | Sub-city area |
| `territory` | category | Sales territory |
| `distributor` | category | Distributor name |
| `route` | category | Distribution route |
| `customer` | category | Retail outlet / customer name |
| `brand` | category | Product brand |
| `variant` | category | Product variant |
| `packtype` | category | Pack type (bottle, sachet, etc.) |
| `sku` | category | Stock-keeping unit code |
| `sales` | float32 | Secondary / offtake sales |
| `primary sales` | float32 | Primary / depot sales |
| `target` | float32 | Sales target |
| `productivity` | float32 | Productive outlet count or ratio |
| `mro` | float32 | Must-range outlet count |
| `unproductive_mro` | float32 | MRO outlets with zero sales |
| `unassorted_mro` | float32 | MRO outlets missing assortment |
| `stockout_mro` | float32 | MRO outlets with stockouts |
| `stockout` | float32 | Stockout count |
| `assortment` | float32 | Assortment score |
| `mto` | float32 | Must-take-order metric |

> **Memory tip:** A 14 M-row file drops from ~8 GB (naïve `read_csv`) to ~1.5 GB with categorical dtypes and float32 downcast — a ~80% reduction.

---

## 💬 Sample Questions to Get Started

```text
# Sales performance
"Which region has the highest sales this year?"
"Top 5 SKUs by primary sales"
"Monthly sales trend by brand"
"Compare target vs actual sales by city"

# Distribution health
"Total stockout brands in April"
"Which distributor has the lowest productivity?"
"Unproductive MRO breakdown by territory"
"Assortment score by area"

# Multi-turn deep dives
"Which brand had the highest sales in Q1?"
  → "Break that down by city."
    → "Which city underperformed vs target the most?"
```

---

## 🏗️ How It Works

```
User types question
      │
      ▼
  ui.py — _submit_question()
      │
      ├─ chat_history.py  →  stores user message
      │
      ├─ query_engine.py  →  run_query(engine, question)
      │       │
      │       ├─ Serialises ConversationBufferMemory to text
      │       ├─ Calls LangChain AgentExecutor with full context
      │       │       │
      │       │       └─ create_pandas_dataframe_agent
      │       │               ├─ Writes pandas code
      │       │               ├─ Executes on full 14 M-row DataFrame
      │       │               └─ Returns str / DataFrame / number
      │       │
      │       ├─ Saves turn to memory
      │       └─ Returns QueryResult(success, data, is_table, is_number, ...)
      │
      ├─ chat_history.py  →  stores AI response
      └─ st.rerun()       →  re-renders chat UI
```

---

## 🔧 Configuration

All settings live in `app/config.py`:

```python
DEFAULT_MODEL: str = "gpt-4.1-mini"   # change to "gpt-3.5-turbo" to save cost

AVAILABLE_MODELS: List[str] = [
    "gpt-4.1-mini",   # Best value — fast, cheap, tool-calling support
    "gpt-4.1",        # Most capable
    "gpt-4o",         # Multimodal powerhouse
    "gpt-4o-mini",    # Fast and affordable
    "gpt-4-turbo",    # Legacy GPT-4 Turbo
]
```

You can also switch models live from the sidebar — the engine and memory reset automatically.

---

## 🛠️ Troubleshooting

**`OPENAI_API_KEY not found` in sidebar**
Make sure `.env` is in the project root (not inside `app/`), the key starts with `sk-`, and your virtual environment is active.

**`pip dependency conflict — pandasai requires openai<2`**
You have a leftover PandasAI install. Fix:
```bash
pip uninstall pandasai -y && pip install -r requirements.txt
```

**Queries time out on large data**
Large aggregations on 14 M rows can take 30–60 s on first run. To speed up repeated loads, convert your dataset to Parquet:
```bash
python -c "import pandas as pd; df = pd.read_csv('data/file.gz', compression='gzip'); df.to_parquet('data/file.parquet', index=False)"
```

**Port 8501 already in use**
```bash
streamlit run app.py --server.port 8502
```

---

## 🚀 Extending the Project

### Add Claude (Anthropic) as LLM
```bash
pip install langchain-anthropic
```
```python
# In app/query_engine.py
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key=api_key)
```

### Speed up queries with DuckDB
```python
import duckdb
conn = duckdb.connect()
conn.register("sales", df)
result = conn.execute("SELECT region, SUM(sales) FROM sales GROUP BY 1 ORDER BY 2 DESC").df()
```

### Deploy to Streamlit Community Cloud
1. Push to GitHub — confirm `data/` and `.env` are in `.gitignore`
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select your repo
3. Under **Advanced settings → Secrets**, add:
```toml
OPENAI_API_KEY = "sk-proj-..."
```
4. Upload your dataset via the sidebar file uploader (Community Cloud has no persistent disk)

---

## 📦 Requirements

```
streamlit>=1.32.0
pandas>=2.1.0
pyarrow>=14.0.0
openpyxl>=3.1.0
langchain>=0.2.0
langchain-openai>=0.1.0
langchain-experimental>=0.0.60
openai>=1.0.0
python-dotenv>=1.0.0
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for full terms.

---

## 🙏 Acknowledgements

- [LangChain](https://www.langchain.com/) — agent orchestration and conversational memory
- [Streamlit](https://streamlit.io/) — rapid data app framework
- [OpenAI](https://openai.com/) — GPT-4.1 language model
- [pandas](https://pandas.pydata.org/) — the data manipulation backbone

---

<div align="center">

**Built by [Shuaib Iqbal](https://shuaibiqbal.github.io/portfolio)** &nbsp;·&nbsp; [GitHub](https://github.com/your-username/sales-chat-ai) &nbsp;·&nbsp; [Portfolio](https://shuaibiqbal.github.io/portfolio)

*If this helped you, drop a ⭐ on the repo — it means a lot!*

</div>
