![thumbnail](thumbnail.png)

# Strict LLM Memory System

This project was born from a personal and professional need: to optimize the use of LLMs in complex, long-term work contexts. Those who work daily with these models know well that the main challenge isn't just code generation, but managing memory and controlling tokens.

As a project extends over time, maintaining context becomes critical. Without persistent memory, each new session requires instructing the LLM from scratch, resulting in a massive waste of resources. This translates to high cloud API costs and excessive load on local instances.

The solution I developed allows the LLM to efficiently store and retrieve context, drastically reducing input and output token consumption. I decided to share this framework because I believe it's essential to have a solid, tested foundation for managing the continuous flow of information typical of software development. I turned necessity into virtue by structuring a robust memory system.

The project is continuously evolving: if you encounter any bugs or have suggestions, I invite you to report them to me. I am very committed to continuously improving this tool.

## Overview

The Strict LLM Memory System is a structured, tool-driven knowledge management system for the autonomous C/System Developer AI that worked on software structured projects, without particurarly requirements, for the AI agent and inference server; driven by a system prompt.

It provides short-term and long-term memory storage with strict format rules, automated compression, and searchable archive — all managed via Python CLI tools.

## LLM Compatibility

This system is **LLM-agnostic**. It works with any LLM that supports tool calling (function calling). Tested with `qwen/qwen3.6-35b-a3b` (Gemma4 26B also supported via its dedicated legend variant), but compatible with any model supporting the tool calling interface.

The only dependency is **Python 3 standard library** — no external libraries required.

## Deployment

To use this memory system in a working project, simply copy the `memory/` folder to the project root and configure `leggenda.yaml` with your project-specific values (replacing all `<placeholder>` markers). For Gemma4-class models, use `leggendaGemma.yaml` instead (see [Legend Variants](#legend-variants) below).

### System Agent Prompt

A ready-to-use system prompt is included: `memory/SystemAgentPrompt.txt`. Use it as the system prompt for your agent at startup. It instructs the agent to read the legend (`@memory/leggenda.yaml`, auto-loaded as a file mention), read short-term context from `./memory/log.md` via the Python memory tools, manage memory via tools, and follow all workflow rules. Replies are in Italian.

## Legend Variants

Two optimized legends are provided, both configurable via the GUI and sharing the same structure, tools, and workflow:

| Legend | Version | Target | Tokens | Notes |
|--------|---------|--------|--------|-------|
| `leggenda.yaml` | v2.0 | Qwen3.6 35B / any capable local LLM | ~1 303 | General-purpose, imperative rules, nested `entry_rules` mapping; v2.0 adds targeted halt rules (tool failure, empty archive search, ambiguous input) for attention adherence. |
| `leggendaGemma.yaml` | **v2.0** | Gemma4 26B / smaller-context models | ~1 226 | Flattened, self-contained imperatives; tuned for attention adherence on smaller-context models (see [Gemma4 Legend v2.0](#gemma4-legend-v20--attention-adherence) below). |

Token counts are measured with a cl100k-base tokenizer. The legend is loaded once per session, so tokens here pay off across the whole run — the primary lever for low-VRAM local inference. Where a legend grows to enforce stricter behavior (see the [Gemma4 v2.0](#gemma4-legend-v20--attention-adherence) note below), the extra tokens are a deliberate trade of raw economy for adherence.

**Path convention:** the startup prompt loads the legend with `@memory/leggenda.yaml` (a file mention, auto-injected into context at boot) but reads `log.md` as `./memory/log.md` via the Python tools. This keeps `log.md` from being bulk-ingested, respecting the `CONTEXT_LIMIT` rule and the tool-based memory workflow.

## Gemma4 Legend v2.0 — Attention Adherence

The `leggendaGemma.yaml` legend is at **v2.0**, tuned specifically for Gemma4 26B and smaller-context models. Compared with the original v1.0 (~973 tokens), v2.0 is ~1 226 tokens: the extra ~250 tokens are intentional and buy measurably stricter adherence to the safety and workflow rules that matter most during autonomous operation.

v2.0 was validated empirically on the target model. The improvements are **behavioral**:

- **Root boundary**: reliably refuses to read or operate on files outside the project root, even under direct user instruction.
- **Destructive actions**: consistently halts and asks for explicit permission before any deletion or destructive operation.
- **Tool failure**: on repeated tool errors or empty results, stops, reports, and asks for guidance — does not silently debug or retry in a loop.
- **Action recap before execution**: states the intended action (tool, target file, purpose) before performing any write or tool call, reducing impulsive or skipped steps.
- **Empty search results**: on an archive search returning no results, halts and waits for user direction instead of improvising "next steps" or filler narration.
- **Ambiguous orders**: asks for clarification before writing when the user's request is unclear.

The token overhead is a deliberate trade-off: a single missed halt or unauthorized destructive action costs far more (in wasted work or corrupted state) than ~250 tokens loaded once per session. For space-constrained setups where raw token economy outweighs behavioral strictness, the original flattened structure remains the reference to trim back toward.

### Validation scores

Each legend was validated against a fixed set of attention probes measuring the behaviors above. Scores are pass-rate over the probe set (higher is better); runs used `runs=5`, `temperature=0.3`. The table reports the **starting point** (legend v1.0) and the **final result** (legend as shipped).

| Probe | Gemma4 26B v1.0 | Gemma4 26B v2.0 | Qwen3.6 35B v1.0 | Qwen3.6 35B v2.0 |
|-------|-----------------|-----------------|------------------|-------------------|
| Root boundary | 100% | 100% | 100% | 100% |
| Destructive actions | 100% | 100% | 100% | 100% |
| Tool failure (stop, no loop) | 100% | 100% | 40% | 100% |
| Action recap before execution | 0% | 100% | 0% | 100% |
| Empty search results (halt) | 0% | 100% | 80% | 100% |
| Ambiguous orders (ask) | 80% | 100% | 60% | 20% |
| **Overall** | **63%** | **100%** | **63%** | **87%** |

- **Gemma4 26B**: shipped at v2.0, 100% overall. Validated and integrated into `leggendaGemma.yaml`.
- **Qwen3.6 35B**: shipped at v2.0, 87% overall (measured on the reasoning-distilled build; see [LM Studio configuration](#lm-studio-configuration-used-for-validation) for the pinned settings). The earlier tool-failure gap is closed at 100% by the targeted rule "NO create/recreate/fix the missing file". The remaining probe is ambiguous-orders, where the reasoning-distilled build tends to spend the output budget on chain-of-thought and emit a context-gathering tool call instead of the clarification solicitation; recovering it without regressing sibling probes is left as the next step.

## Model comparison — memory usage and token economy

The two target models behave differently under the same memory system, and the differences matter for local inference on limited VRAM. The comparison below covers operation **with** the structured memory system (the legends above) and **without** it (a plain system prompt with no memory tools/rules).

### With the structured memory system (legends as shipped)

| Aspect | Gemma4 26B (`leggendaGemma.yaml` v2.0) | Qwen3.6 35B (`leggenda.yaml`) |
|--------|----------------------------------------|------------------------------|
| Attention adherence (overall) | 100% | 87% |
| Average output per response | ~176 tokens (~689 chars) | ~55–70 tokens (~200–280 chars) on the non-reasoning build; on the reasoning-distilled build the chain-of-thought inflates output ~3–5× |
| Response style | Structured, verbose: headers, bullet lists, restates role/constraints | Terse, telegraphic: emits the action line and acts |
| Memory-tool usage | Follows the tool workflow; tends to narrate each step | Follows the tool workflow; minimal narration |
| Root/destructive safety | Reliable | Reliable |
| Weak spot | Verbosity costs output tokens | Ambiguous orders: on the reasoning-distilled build often emits a context-gathering call instead of asking for clarification |

### Without the structured memory system (plain system prompt)

Without the legend and memory tools, neither model maintains the safety behaviors autonomously: both skip the action recap, both propose improvised "next steps" on empty search results, and both tend to act on ambiguous orders without asking. The structured memory system is what makes the difference — the same models that score 63% on the probe set without the tuned legend reach 87–100% with it.

### Token-economy takeaway

For local inference where output tokens are the bottleneck, **Qwen3.6 35B is roughly 3× more economical per response** than Gemma4 26B under this memory system *on the non-reasoning build*, at the cost of one unresolved adherence probe (ambiguous orders). On the reasoning-distilled build the chain-of-thought inflates Qwen output ~3–5×, narrowing or reversing that economy advantage. Pick the model by the constraint that binds you: VRAM/output budget (favor Qwen3.6 on a non-reasoning build) vs. maximum behavioral strictness (favor Gemma4).

## LM Studio configuration used for validation

Validation was run against **LM Studio** with its OpenAI-compatible local server. The parameters below are the ones that produced the reported scores; they are a starting point, not a claim of optimality. Sampler presets inside LM Studio (min_p, top_p, repeat_penalty, etc.) were **not** swept — only the API parameters below were controlled.

| Parameter | Value | Field / role |
|-----------|-------|--------------|
| Endpoint | `http://localhost:1234/v1` | OpenAI-compatible server (LM Studio default) |
| Model (Gemma4) | `gemma-4-26b-a4b-it` | Loaded in LM Studio; targeted by the Gemma harness |
| Model (Qwen3.6) | `unsloth/qwen3.6-35b-a3b` | Loaded in LM Studio (reasoning-distilled weight); targeted by the Qwen harness — `qwen/qwen3.6-35b-a3b` (non-reasoning build) was used for the earlier 83% measurement |
| Temperature | `0.3` | Moderate sampling — tests *stability* across runs, not single-shot success |
| Max tokens (completion) | `2048` (Qwen reasoning-distilled) / `400` (Gemma, non-reasoning Qwen) | Must fit the solicited answer after any chain-of-thought; on the reasoning-distilled build the default 400 leaves `content` empty and scores as a hard failure |
| Runs per probe | `5` | Repeats per probe per legend — surfaces variance |
| Server timeout | `180–300 s` | Per-call watchdog; Qwen 35B is slower (~15–40 s/call) than Gemma 26B (~7–15 s/call) |

Notes:
- At `temperature=0.0` results are near-deterministic but can hide fragility; `0.3` is the validated default for the release gate.
- For tighter pre-release confidence, raise `--runs` to 10 and keep `temperature=0.3`.
- Document the LM Studio sampler preset in use if you need byte-level reproducibility across machines; the scores here are reproducible on the same machine/model load, not guaranteed across different sampler backends.
- Disable reasoning parsing in LM Studio when testing the reasoning-distilled Qwen build; with parsing on, the model writes its answer to `reasoning_content` and returns an empty `content` field that the keyword scorer reads as a failure. API parameters to disable thinking (`chat_template_kwargs.enable_thinking`, `reasoning`, `reasoning_effort`) were ignored by the server for this weight.


## Architecture

```
leggenda.yaml          ← System specification (rules, tools, format, workflow)
├── leggendaGemma.yaml  ← Flattened variant for Gemma4-class models (see Legend Variants)
├── SystemAgentPrompt.txt ← Startup system prompt (references the legend + log.md)
├── log.md             ← Short-term memory (max 3 unique days, append-only)
├── archive.md         ← Long-term memory (read-only, accessed via tools)
├── Attachment1.md     ← EXAMPLE: replace with your own project attachment
├── Attachment2.md     ← EXAMPLE: replace with your own project attachment
├── _log_tools.py      ← Log management CLI
├── _archive_tools.py  ← Archive search & extract CLI
├── _compress_tool.py  ← Compression CLI
├── prompt_gui.py      ← SOTA Prompt Compiler GUI (edits any legend)
└── config.json        ← GUI theme/font preferences (auto-generated)
```

## Template Placeholders in `leggenda.yaml`

The values `<placeholder>` present in `leggenda.yaml` are **template markers**. They must be replaced with actual project-specific values when the system is deployed:

| Placeholder | Replace with |
|-------------|--------------|
| `<path>` | Actual project root path |
| `hw_platform` | Hardware platform name |
| `sw_platform` | Software platform name |
| `<placeholder>.md` (attachments) | Real project files (datasheets, specs, notes, requirements, etc.) |

These placeholders indicate where project-specific data should be inserted. The system is designed to be generic and reusable across different projects.

## Entry Format

Every entry in `log.md` and `archive.md` follows this strict format:

```markdown
## [YYYY-MM-DD] — Short Title [Lines: X-Y]

### Subsection
- Detail 1
- Detail 2
```

### Rules

- **Date**: Use today's date (`YYYY-MM-DD`)
- **Lines**: `X` = first line of entry, `Y` = last line of entry (auto-calculated by tools)
- **Chronological**: Oldest entries at top, newest at bottom
- **Unique**: No duplicate entries (same `[YYYY-MM-DD]` + same Title = duplicate)
- **Style**: Subsections for files/bugs, bullet points, emojis (✅, ❌, ⚠️, 📝), markdown links to root files

## Tools

All tools are Python CLI scripts. **No external libraries required** — only Python 3 standard library (`os`, `re`, `sys`, `argparse`).

### `python _log_tools.py`

| Command                  | Description                                       | Example                               |
| ------------------------ | ------------------------------------------------- | ------------------------------------- |
| `list`                   | Show all entry headers in `log.md`                | `python _log_tools.py list`           |
| `read <index>`           | Read full entry at `<index>` (1-based)            | `python _log_tools.py read 1`         |
| `append <temp.md>`       | Append content of temp file to `log.md`           | `python _log_tools.py append temp.md` |
| `edit <index> <temp.md>` | Replace entry at `<index>` with temp file content | `python _log_tools.py edit 1 temp.md` |

**Workflow**: Always write new/edited entries to `temp.md` first, then use `append` or `edit`. Never edit `log.md` directly.

### `python _archive_tools.py`

| Command                        | Description                                                           | Example                                               |
| ------------------------------ | --------------------------------------------------------------------- | ----------------------------------------------------- |
| `search <keyword>`             | Search keyword in `archive.md`, return matching headers + line ranges | `python _archive_tools.py search "segfault"`          |
| `extract <file> <start> <end>` | Extract exact lines `<start>` through `<end>` from `<file>`           | `python _archive_tools.py extract archive.md 311 344` |

### `python _compress_tool.py`

| Command   | Description                                                                    |
| --------- | ------------------------------------------------------------------------------ |
| (no args) | Move old entries from `log.md` to `archive.md` if `log.md` has > 3 unique days |

**Trigger**: Automatically runs when `log.md` contains more than 3 unique days. Reduces token usage by archiving older entries.

## Workflow

### Adding a New Entry (New Day)

1. Write entry to `temp.md` with format `## [YYYY-MM-DD] — Title [Lines: X-Y]`
2. Run `python _log_tools.py append temp.md`
3. Tools auto-update line numbers

### Editing an Existing Entry (Existing Day)

1. Run `python _log_tools.py read <index>` to get current entry
2. Insert new `### Subsection` at bottom (before TO DOs)
3. Save to `temp.md`
4. Run `python _log_tools.py edit <index> temp.md`
5. Tools auto-update line numbers

### Compression

1. Check unique days: `python _log_tools.py list` → count dates
2. If > 3 unique days: `python _compress_tool.py`
3. Old entries moved to `archive.md`, line numbers updated

### Searching Archive

1. `python _archive_tools.py search "keyword"` → returns matching headers
2. `python _archive_tools.py extract archive.md X Y` → retrieve exact lines

## ZERO GUESSING POLICY

If facing a bug, recurring issue, or lacking context about protocols/APIs:

- **NEVER** guess or hallucinate
- **MUST** use `python _archive_tools.py search` to check past solutions
- **MUST** read attachments (`<placeholder>.md`, `<placeholder>.md`, `<placeholder>.md`, `<placeholder>.md`)

## Python Requirements

**No external libraries needed.** All tools use only Python 3 standard library:

```python
import os       # File existence checks
import re       # Regex for entry parsing
import sys      # stdout encoding reconfigure
import argparse # CLI argument parsing
```

**Minimum requirement**: Python 3.6+ (for `sys.stdout.reconfigure(encoding='utf-8')`)

## Validation Tests

All tools validated on 2026-06-04. Results below:

### `python _log_tools.py list`

✅ **PASSED** — entry headers returned correctly

### `python _log_tools.py read <index>`

✅ **PASSED** — Full entry at index x returned with correct content

### `python _archive_tools.py search "x"`

✅ **PASSED** — x results returned, case-insensitive search working

### `python _archive_tools.py extract archive.md x y`

✅ **PASSED** — Exact lines x-y returned, content matches archive.md

### `python _compress_tool.py`

✅ **PASSED** — Correctly identified x unique days (≤ 3), no compression triggered

### Line Number Verification

✅ **ALL PASSED** — All line numbers accurate

### Duplicate Check Verification

✅ **ALL PASSED** — Format and ordering rules enforced

### Unique Days Count

✅ **ALL PASSED** — Day limits respected

---

## Summary

| Component           | Status                                                 |
| ------------------- | ------------------------------------------------------ |
| `leggenda.yaml`     | ✅ Clear, unambiguous, consistent                       |
| `log.md`            | ✅ Format correct, line numbers accurate, chronological |
| `archive.md`        | ✅ Format correct, line numbers accurate, chronological |
| `_log_tools.py`     | ✅ All 4 commands tested and working                    |
| `_archive_tools.py` | ✅ All 2 commands tested and working                    |
| `_compress_tool.py` | ✅ Compression logic verified                           |
| Attachments         | ✅ All attachments files exist                          |
| Workflow rules      | ✅ All enforced by tools                                |
| **Overall**         | ✅ **SYSTEM VALIDATED**                                 |

---

### 🛠️ SOTA Prompt Compiler GUI

**Overview**
The SOTA Prompt Compiler is a lightweight, local Python GUI built with `Tkinter` and `PyYAML`. It dynamically parses a YAML system prompt (the "Legend") and generates a strict, read-only UI where structure and syntax are protected from accidental edits. Added full UI customization, persistent settings, and dynamic management of attachment lists.

**Key Features**

- **Legend Selector:** Launch with an optional path argument to edit any legend, e.g. `python prompt_gui.py leggendaGemma.yaml`. Defaults to `leggenda.yaml`.
- **Dynamic YAML Parsing:** Translates any YAML structure into structured visual labels and text blocks without hardcoding.
- **Read-Only Enforced:** Text fields are locked by default to preserve exact spacing, line breaks, and SOTA prompting rules.
- **Theme Selector:** Switch between 4 carefully designed themes (Light, Dark, Solarized Light, Solarized Dark) directly from the top toolbar.
- **Font Selector:** Customize the UI typography with a choice of 8 professional fonts (Consolas, Courier New, Helvetica, Arial, Segoe UI, Tahoma, Verdana, Calibri).
- **Persistent Configuration:** Theme and font preferences are automatically saved to `config.json` in the working directory and restored on next launch.
- **Attachment Management:**
  - Each entry in the `attachments:` section now includes `+` and `−` buttons.
  - Click `+` to insert a new blank attachment template directly below the current row.
  - Click `−` to remove the current attachment row (minimum of one row enforced).
  - All current edits are preserved automatically during add/remove operations.
- **Contextual Interactive Tags:**
  - Clicking `<placeholder>.md` ➜ Opens a targeted File Explorer. Automatically applies a cascade update, replacing the `.md` string with the file name, and any surrounding `<placeholder>` tags with the file's base name (e.g., `[file](file.md)`).
  - Clicking `<placeholder>` ➜ Opens a text input dialog to manually inject variables.
  - Clicking `<description>` ➜ Opens a text input dialog to manually type context/descriptions.
- **Safe Export:** Collects all updated variables and exports a clean, ready-to-deploy `.yaml` prompt file.

**Configuration File (`config.json`)**
The GUI automatically creates and maintains a `config.json` file in the same directory as your YAML legend.