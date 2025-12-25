# 🚀 Kasparro AI Agentic Content Generation System

A modular, multi-agent automation system that transforms raw, unstructured product data into production-ready, structured content for e-commerce websites.

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Quick Start](#3-quick-start)
4. [Project Structure](#4-project-structure)
5. [Input & Output](#5-input--output)
6. [Agents & Components](#6-agents--components)
7. [Running Tests](#7-running-tests)
8. [Logging & Observability](#8-logging--observability)
9. [Troubleshooting](#9-troubleshooting)
10. [API Rate Limits](#10-api-rate-limits)

---

## 1. Overview

Unlike simple LLM wrappers, this system uses a **Directed Acyclic Graph (DAG)** architecture where distinct "Agents" handle specific responsibilities:

- **Parsing** → Extracts structured data from raw text
- **Strategy** → Generates FAQs and competitor analysis
- **Content Generation** → Creates marketing copy
- **Assembly** → Builds final JSON outputs

The system enforces strict data contracts using **Pydantic models** to ensure the final output is always machine-readable JSON.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PIPELINE FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Raw Text]  →  [Parser Agent]  →  [Internal Model]            │
│       │              │                    │                     │
│       └──────────────┴────────────────────┘                     │
│                           ↓                                     │
│              [Strategy Agent]                                   │
│              ├── Generate FAQs                                  │
│              └── Create Competitor                              │
│                           ↓                                     │
│              [Logic Blocks]                                     │
│              ├── Benefits Block                                 │
│              ├── Usage Block                                    │
│              └── Comparison Block                               │
│                           ↓                                     │
│              [Builder Agent]                                    │
│                           ↓                                     │
│  ┌────────────────┬────────────────┬────────────────┐          │
│  │ product_page   │   faq.json     │ comparison_    │          │
│  │    .json       │                │   page.json    │          │
│  └────────────────┴────────────────┴────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow Steps:

1. **Ingestion (Parser Agent)** - Reads raw text, extracts entities into `ProductData`
2. **Strategy (Strategy Agent)** - Generates FAQ questions and fictional competitor
3. **Content Generation (Logic Blocks)** - Creates marketing copy, usage steps, comparisons
4. **Assembly (Builder Agent)** - Builds final JSON files with validated schemas

---

## 3. Quick Start

### Prerequisites

- **Python 3.10+**
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/apikey))

### Step 1: Clone & Install

```bash
# Clone the repository
git clone <your-repo-url>
cd kasparro-ai-agentic-content-generation-system

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

### Step 3: Run the Pipeline

```bash
# Windows PowerShell
$env:PYTHONPATH = "."
python -m src.main

# Windows CMD
set PYTHONPATH=.
python -m src.main

# Linux/Mac
PYTHONPATH=. python -m src.main
```

### Step 4: Check Output

After successful execution, find your generated files in:
- `output/product_page.json`
- `output/faq.json`
- `output/comparison_page.json`

---

## 4. Project Structure

```
kasparro-ai-agentic-content-generation-system/
│
├── data/
│   └── raw_input.txt           # Input: Raw product data
│
├── output/                      # Output: Generated JSON files
│   ├── product_page.json
│   ├── faq.json
│   └── comparison_page.json
│
├── logs/
│   └── system.log              # Detailed execution logs
│
├── src/
│   ├── agents/                  # Agent implementations
│   │   ├── parser_agent.py     # Parses raw text → ProductData
│   │   ├── strategy_agent.py   # Generates FAQs & competitor
│   │   └── builder_agent.py    # Assembles final JSON pages
│   │
│   ├── blocks/                  # Reusable logic blocks
│   │   ├── benefits.py         # Marketing copy generator
│   │   ├── usage.py            # Usage step formatter
│   │   └── comparison.py       # Product comparison logic
│   │
│   ├── models/                  # Pydantic data models
│   │   ├── internal.py         # ProductData, CompetitorData
│   │   └── output.py           # FAQPage, ProductPage, ComparisonPage
│   │
│   ├── utils/                   # Utilities
│   │   ├── llm_client.py       # Gemini API client
│   │   └── logger.py           # Professional logging
│   │
│   └── main.py                  # Main pipeline entry point
│
├── tests/
│   └── test_integrity.py       # Output validation tests
│
├── .env                         # API key (create this!)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 5. Input & Output

### Input Format

Place your product data in `data/raw_input.txt`:

```text
Product Name: RenewAge Retinol Night Cream
Concentration: 0.3% Encapsulated Retinol + Peptides
Price: ₹899

Skin Type: Normal, Dry, Combination, Oily

Key Ingredients:
- 0.3% Encapsulated Retinol
- Ceramides (NP, AP, EOP)
- Peptide Complex (Matrixyl 3000)

Benefits:
- Accelerates cell turnover
- Reduces wrinkles and fine lines
- Strengthens skin barrier

How to Use: Use only in PM routine. Apply pea-sized amount...

Side Effects: Purging may occur during first 2-4 weeks...
```

### Output Files

| File | Description |
|------|-------------|
| `product_page.json` | Product title, price, benefits, usage guide, ingredients |
| `faq.json` | Categorized Q&A (Usage, Safety, Ingredients) |
| `comparison_page.json` | Side-by-side comparison with fictional competitor |

---

## 6. Agents & Components

### A. Agents (Orchestrators)

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Parser Agent** | The Reader | Extracts structured data from raw text |
| **Strategy Agent** | The Planner | Generates FAQ questions & competitor attributes |
| **Builder Agent** | The Assembler | Builds final JSON outputs |

### B. Logic Blocks (Workers)

| Block | Function | Input → Output |
|-------|----------|----------------|
| **Benefits Block** | Marketing copy | `ingredients` → `bullet points` |
| **Usage Block** | Step formatting | `raw_text` → `numbered steps` |
| **Comparison Block** | Analysis | `ProductA + ProductB` → `comparison table` |

### C. Data Models (Guardrails)

- **`ProductData`** - Internal product representation
- **`CompetitorData`** - Fictional competitor schema
- **`FAQPage`** / **`ProductPage`** / **`ComparisonPage`** - Output schemas

---

## 7. Running Tests

Validate that your output files are correctly structured:

```bash
# Windows PowerShell
$env:PYTHONPATH = "."
python -m pytest tests/test_integrity.py -v

# Linux/Mac
PYTHONPATH=. python -m pytest tests/test_integrity.py -v
```

### Expected Output:
```
tests/test_integrity.py::test_output_files_exist PASSED
tests/test_integrity.py::test_product_page_schema PASSED
tests/test_integrity.py::test_faq_page_logic PASSED
tests/test_integrity.py::test_comparison_winner PASSED

============================== 4 passed ==============================
```

---

## 8. Logging & Observability

The system uses professional logging with dual output:

- **Console**: Real-time progress (INFO level)
- **File**: Detailed trace (`logs/system.log`)

### Sample Console Output:
```
INFO | KASPARRO AI CONTENT ENGINE - Pipeline Started
INFO | [THOUGHT] Phase 1: Parsing raw product data
INFO | [OK] Data parsed successfully: RenewAge Retinol Night Cream
INFO | [THOUGHT] Phase 2: Strategy generation
INFO | [OK] Competitor generated: LumiGlow Overnight Cream
INFO | [FILE] Saved: output\product_page.json
INFO | PIPELINE COMPLETE
```

### View Detailed Logs:
```bash
# Windows
type logs\system.log

# Linux/Mac
cat logs/system.log
```

---

## 9. Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'src'`

**Solution**: Set PYTHONPATH before running:
```bash
# Windows PowerShell
$env:PYTHONPATH = "."
python -m src.main
```

### Issue: `GEMINI_API_KEY not found in .env file`

**Solution**: Create `.env` file in project root:
```env
GEMINI_API_KEY=your_api_key_here
```

### Issue: `429 You exceeded your current quota`

**Solution**: See [API Rate Limits](#10-api-rate-limits) section.

### Issue: Unicode/Emoji errors on Windows

**Solution**: The logging system automatically handles this. If issues persist, ensure your terminal supports UTF-8.

---

## 10. API Rate Limits

The Gemini API has **free tier limits**:

| Model | Daily Limit | Requests/Minute |
|-------|-------------|-----------------|
| gemini-2.5-flash | 20/day | 2/min |
| gemini-2.5-flash-lite | 20/day | 2/min |
| gemini-2.5-pro | 5/day | 2/min |

### If You Hit Rate Limits:

1. **Wait** - Quotas reset daily at midnight (Pacific Time)
2. **New API Key** - Create a new key at [AI Studio](https://aistudio.google.com/apikey)
3. **Upgrade** - Consider paid tier for higher limits

### Change Model (Optional):

Edit `src/utils/llm_client.py`:
```python
MODEL_NAME = "gemini-2.5-flash-lite"  # Change to preferred model
```

---

## 📄 License

MIT License

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

**Built with ❤️ using Google Gemini AI**
