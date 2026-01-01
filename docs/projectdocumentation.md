# Project Documentation: Multi-Agent Content Generation System

---

## 1. Problem Statement

Design and implement a **modular agentic automation system** that:
- Takes unstructured product data as input
- Automatically generates structured, machine-readable content pages
- Operates via autonomous agents (not a monolithic script)
- Produces FAQ, Product Description, and Comparison pages as JSON output

The system must demonstrate:
- Multi-agent workflows with clear boundaries
- Automation graphs / orchestration patterns
- Reusable content logic blocks
- Template-based generation
- Machine-readable JSON output

---

## 2. Solution Overview

This system implements a **True Multi-Agent Architecture** where:

| Principle | Implementation |
|-----------|----------------|
| **Agent Autonomy** | Each agent plans and executes independently |
| **Dynamic Coordination** | Orchestrator assigns tasks by capability matching |
| **Message-Based Communication** | Agents communicate via publish-subscribe message bus |
| **Shared Knowledge** | Blackboard pattern for indirect data exchange |
| **Dependency-Aware Execution** | DAG-based task scheduling |

**Key Components:**
- **Orchestrator**: Manages agent lifecycle and task coordination
- **3 Autonomous Agents**: Parser, Strategy, Builder
- **Message Bus**: Inter-agent communication
- **Blackboard**: Shared state management
- **Template Engine**: Schema-based content assembly
- **Logic Blocks**: Reusable transformation functions

---

## 3. Scopes & Assumptions

### Scope
- Processes skincare/cosmetic product data (extensible to other domains)
- Generates 3 content pages: FAQ, Product, Comparison
- Produces minimum 15 categorized FAQ questions
- Creates fictional competitor (Product B) for comparison

### Assumptions
- Input is text-based (`data/raw_input.txt`)
- External LLM (Google Gemini) available for semantic processing
- Single-run pipeline (not persistent/streaming)
- English language content only

### Constraints
- Agents rely only on provided context (no external knowledge)
- All output must be valid JSON (Pydantic-validated)
- No human intervention during execution

---

## 4. System Design

### 4.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATOR                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Agent Registry  │  │   Task Queue    │  │   Dependency Resolution     │  │
│  │ (Capability Map)│  │ (Priority-based)│  │   (DAG Scheduling)          │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│   PARSER AGENT    │   │  STRATEGY AGENT   │   │   BUILDER AGENT   │
│                   │   │                   │   │                   │
│ Capabilities:     │   │ Capabilities:     │   │ Capabilities:     │
│ • parse_raw_data  │   │ • gen_competitor  │   │ • build_product   │
│ • validate_data   │   │ • generate_faqs   │   │ • build_faq       │
│                   │   │                   │   │ • build_comparison│
│ State Machine:    │   │ State Machine:    │   │ State Machine:    │
│ IDLE → THINKING   │   │ IDLE → THINKING   │   │ IDLE → THINKING   │
│ → EXECUTING       │   │ → EXECUTING       │   │ → EXECUTING       │
│ → COMPLETED       │   │ → COMPLETED       │   │ → COMPLETED       │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              ┌─────▼─────┐               ┌─────▼─────┐
              │  MESSAGE  │               │ BLACKBOARD│
              │    BUS    │               │ (Shared   │
              │           │               │   State)  │
              │ • Pub/Sub │               │           │
              │ • Routing │               │ • Data    │
              │ • History │               │ • Results │
              └───────────┘               └───────────┘
```

### 4.2 Task Dependency DAG

```
                    ┌─────────────────┐
                    │   PARSE TASK    │
                    │   Priority: 1   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
    ┌─────────────────┐      │    ┌─────────────────┐
    │ COMPETITOR TASK │      │    │   FAQ GEN TASK  │
    │   Priority: 2   │      │    │   Priority: 2   │
    └────────┬────────┘      │    └────────┬────────┘
             │               │             │
             │               ▼             │
             │    ┌─────────────────┐      │
             │    │ BUILD PRODUCT   │      │
             │    │   Priority: 3   │      │
             │    └─────────────────┘      │
             │                             │
             ▼                             ▼
    ┌─────────────────┐         ┌─────────────────┐
    │ BUILD COMPARISON│         │   BUILD FAQ     │
    │   Priority: 3   │         │   Priority: 3   │
    └─────────────────┘         └─────────────────┘
```

### 4.3 Agent Interaction Sequence

```
┌──────────┐     ┌────────┐     ┌──────────┐     ┌─────────┐     ┌───────────┐
│Orchestrator│   │ Parser │     │ Strategy │     │ Builder │     │ Blackboard│
└─────┬─────┘    └───┬────┘     └────┬─────┘     └────┬────┘     └─────┬─────┘
      │              │               │                │                │
      │ GOAL_ASSIGNED│               │                │                │
      │─────────────>│               │                │                │
      │              │               │                │                │
      │              │ plan()        │                │                │
      │              │───────┐       │                │                │
      │              │       │       │                │                │
      │              │<──────┘       │                │                │
      │              │               │                │                │
      │              │ execute()     │                │                │
      │              │───────┐       │                │                │
      │              │       │       │                │                │
      │              │<──────┘       │                │                │
      │              │               │                │                │
      │              │ post("product_data")           │                │
      │              │────────────────────────────────────────────────>│
      │              │               │                │                │
      │ GOAL_COMPLETE│               │                │                │
      │<─────────────│               │                │                │
      │              │               │                │                │
      │ GOAL_ASSIGNED│               │                │                │
      │─────────────────────────────>│                │                │
      │              │               │                │                │
      │              │               │ read("product_data")            │
      │              │               │────────────────────────────────>│
      │              │               │<────────────────────────────────│
      │              │               │                │                │
      │              │               │ post("competitor_data")         │
      │              │               │────────────────────────────────>│
      │              │               │                │                │
      │              │               │ post("faq_questions")           │
      │              │               │────────────────────────────────>│
      │              │               │                │                │
      │ GOAL_COMPLETE│               │                │                │
      │<─────────────────────────────│                │                │
      │              │               │                │                │
      │ GOAL_ASSIGNED│               │                │                │
      │───────────────────────────────────────────────>│               │
      │              │               │                │                │
      │              │               │                │ read(all_data) │
      │              │               │                │───────────────>│
      │              │               │                │<───────────────│
      │              │               │                │                │
      │              │               │                │ [Logic Blocks] │
      │              │               │                │                │
      │              │               │                │ [Templates]    │
      │              │               │                │                │
      │              │               │                │ post(pages)    │
      │              │               │                │───────────────>│
      │              │               │                │                │
      │ GOAL_COMPLETE│               │                │                │
      │<──────────────────────────────────────────────│                │
      │              │               │                │                │
```

### 4.4 Core Design Patterns

#### Agent Autonomy Pattern
Each agent follows an autonomous goal-driven lifecycle:

```
┌─────────────┐
│    IDLE     │◄──────────────────────────────────┐
└──────┬──────┘                                   │
       │ receive goal                             │
       ▼                                          │
┌─────────────┐                                   │
│  THINKING   │ ← plan(goal)                      │
└──────┬──────┘                                   │
       │ plan ready                               │
       ▼                                          │
┌─────────────┐                                   │
│  EXECUTING  │ ← execute(plan)                   │
└──────┬──────┘                                   │
       │                                          │
       ├─────────────────┐                        │
       ▼                 ▼                        │
┌─────────────┐   ┌─────────────┐                 │
│  COMPLETED  │   │   FAILED    │                 │
└──────┬──────┘   └──────┬──────┘                 │
       │                 │                        │
       └─────────────────┴────────────────────────┘
```

#### Message-Passing Pattern
Agents communicate without direct coupling:

```
┌──────────────────────────────────────────────────┐
│                   MESSAGE BUS                     │
├──────────────────────────────────────────────────┤
│                                                  │
│  Message Types:                                  │
│  • GOAL_ASSIGNED    (Orchestrator → Agent)       │
│  • GOAL_COMPLETE    (Agent → Orchestrator)       │
│  • TASK_REQUEST     (Agent → Agent)              │
│  • DATA_REQUEST     (Agent → Agent)              │
│  • DATA_RESPONSE    (Agent → Agent)              │
│  • NEED_ASSISTANCE  (Agent → Broadcast)          │
│                                                  │
└──────────────────────────────────────────────────┘
```

#### Blackboard Pattern
Shared knowledge space for indirect coordination:

```
┌──────────────────────────────────────────────────┐
│                   BLACKBOARD                      │
├──────────────────────────────────────────────────┤
│                                                  │
│  Key                │  Owner          │  Tags    │
│  ───────────────────┼─────────────────┼───────── │
│  product_data       │  parser_agent   │  source  │
│  competitor_data    │  strategy_agent │  strategy│
│  faq_questions      │  strategy_agent │  strategy│
│  product_page       │  builder_agent  │  output  │
│  faq_page           │  builder_agent  │  output  │
│  comparison_page    │  builder_agent  │  output  │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 4.5 Template Engine Design

Templates define structured output with:

```
┌─────────────────────────────────────────────────────────────┐
│                    TEMPLATE DEFINITION                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │   FIELDS    │   │    RULES    │   │ DEPENDENCIES│       │
│  │             │   │             │   │             │       │
│  │ • name      │   │ • min_items │   │ • Logic     │       │
│  │ • type      │   │ • format    │   │   Blocks    │       │
│  │ • source    │   │ • validate  │   │             │       │
│  │ • transform │   │             │   │             │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│                             │                               │
│                             ▼                               │
│                    ┌─────────────────┐                      │
│                    │ OUTPUT SCHEMA   │                      │
│                    │ (Pydantic Model)│                      │
│                    └─────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.6 Logic Blocks Design

Reusable transformation functions:

```
┌─────────────────────────────────────────────────────────────┐
│                     LOGIC BLOCKS                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ generate_benefits_block                              │   │
│  │ Input:  ingredients[], benefits[]                    │   │
│  │ Output: marketing_copy[]                             │   │
│  │ Logic:  LLM-based copywriting with constraints       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ extract_usage_block                                  │   │
│  │ Input:  raw_usage_text                               │   │
│  │ Output: numbered_steps[]                             │   │
│  │ Logic:  LLM-based text structuring                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ compare_products_block                               │   │
│  │ Input:  ProductData, CompetitorData                  │   │
│  │ Output: comparison_rows[]                            │   │
│  │ Logic:  Rule-based feature comparison                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.7 Data Flow

```
┌────────────┐
│ raw_input  │
│   .txt     │
└─────┬──────┘
      │
      ▼
┌─────────────┐     ┌─────────────┐
│   PARSER    │────>│ ProductData │
│   AGENT     │     │  (Internal) │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            │            ▼
      ┌─────────────┐      │    ┌─────────────┐
      │  STRATEGY   │      │    │  STRATEGY   │
      │  (Competitor)│     │    │   (FAQs)    │
      └──────┬──────┘      │    └──────┬──────┘
             │             │           │
             ▼             │           ▼
      ┌─────────────┐      │    ┌─────────────┐
      │CompetitorData│     │    │ Questions[] │
      └──────┬──────┘      │    └──────┬──────┘
             │             │           │
             └─────────────┼───────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  BUILDER AGENT  │
                  │  + Logic Blocks │
                  │  + Templates    │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │product_page │   │  faq.json   │   │ comparison_ │
  │   .json     │   │             │   │  page.json  │
  └─────────────┘   └─────────────┘   └─────────────┘
```

---

## 5. Output Specification

All output is machine-readable JSON validated by Pydantic schemas:

| File | Content | Min Requirements |
|------|---------|------------------|
| `product_page.json` | Title, price, description, benefits, usage, ingredients | 3+ benefits |
| `faq.json` | Categorized Q&A pairs | 5+ items, 3+ categories |
| `comparison_page.json` | Feature comparison table, verdict | 4+ comparison rows |

---

## 6. External Dependencies

| Dependency | Purpose |
|------------|---------|
| Google Gemini API | LLM for semantic processing |
| Pydantic | Data validation & JSON serialization |
| python-dotenv | Environment configuration |
