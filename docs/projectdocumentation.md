# Project Documentation: Multi-Agent Content Generation System

## Problem Statement
[cite_start]Design a modular, agentic automation system to convert unstructured product data into structured, machine-readable content pages (FAQ, Product Page, Comparison Page) without human intervention[cite: 4].

## Solution Overview
This system utilizes a **Sequential Multi-Agent Architecture** governed by a strict internal data model. Rather than a monolithic LLM call, the process is broken into distinct "Thinking" (Strategy) and "Doing" (Content Logic) phases. The system ensures deterministic JSON output by validating all data against Pydantic schemas before content generation begins.

## Scopes & Assumptions
* **Scope:** Handles the "GlowBoost" dataset; extensible to other skincare products.
* **Assumption:** The input format remains text-based key-value pairs.
* **Assumption:** External knowledge is restricted; agents rely solely on provided context and internal logic rules.
* **External Tools:** Uses Google Gemini 1.5 Flash via the google-generativeai library for semantic processing and structural enforcement

## System Design

### 1. Architecture Diagram
The system follows a Directed Acyclic Graph (DAG) flow:
`Input -> Parser Agent -> Internal Model -> Strategy Agent -> Content Blocks -> Template Engine -> JSON Output`

### [cite_start]2. Agent Boundaries & Responsibilities [cite: 60]
* **Parser Agent:**
    * *Input:* Raw text string.
    * *Responsibility:* Cleaning, structuring, and validating data into the `Product` schema.
    * *Output:* Validated `Product` object.
* **Strategy Agent:**
    * *Responsibility:* "Creative" tasks—generating user personas for FAQs and conceptualizing the fictional competitor (Product B) based on contrast rules.
    * *Output:* `List[Question]` and `CompetitorData` object.
* **Builder Agent (Template Engine):**
    * *Responsibility:* Orchestrating specific "Logic Blocks" to populate the final JSON templates. It holds no state, only execution logic.

### [cite_start]3. Reusable Logic Blocks [cite: 35]
Logic blocks are pure functions decoupled from the agents:
* `extract_usage_block`: Formats raw usage text into step-by-step lists.
* `generate_benefits_block`: Maps active ingredients to benefits using a pre-defined rule set.
* `compare_ingredients_block`: logical comparison between Product A and Product B attributes.

### 4. Data Flow & Output
Data is passed strictly as Pydantic objects to ensure type safety. [cite_start]The final output is serialized to JSON matching the schema requirements for `faq.json`, `product_page.json`, and `comparison_page.json`[cite: 43].