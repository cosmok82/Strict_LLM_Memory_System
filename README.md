# Strict LLM Memory System

This project was born from a personal and professional need: to optimize the use of LLMs in complex, long-term work contexts. Those who work daily with these models know well that the main challenge isn't just code generation, but managing memory and controlling tokens.

As a project extends over time, maintaining context becomes critical. Without persistent memory, each new session requires instructing the LLM from scratch, resulting in a massive waste of resources. This translates to high cloud API costs and excessive load on local instances.

The solution I developed allows the LLM to efficiently store and retrieve context, drastically reducing input and output token consumption. I decided to share this framework because I believe it's essential to have a solid, tested foundation for managing the continuous flow of information typical of software development. I turned necessity into virtue by structuring a robust memory system.

The project is continuously evolving: if you encounter any bugs or have suggestions, I invite you to report them to me. I am very committed to continuously improving this tool.

## Overview

The Strict LLM Memory System is a structured, tool-driven knowledge management system for the autonomous C/System Developer AI that worked on software structured projects, without particurarly requirements, for the AI agent and inference server; driven by a system prompt.

It provides short-term and long-term memory storage with strict format rules, automated compression, and searchable archive — all managed via Python CLI tools.

## LLM Compatibility

This system is **LLM-agnostic**. It works with any LLM that supports tool calling (function calling). Tested with `qwen/qwen3.6-35b-a3b`, but compatible with any model supporting the tool calling interface.

The only dependency is **Python 3 standard library** — no external libraries required.

## Deployment

To use this memory system in a working project, simply copy the `memory/` folder to the project root and configure `leggenda.yaml` with your project-specific values (replacing all `<placeholder>` markers).

### System Agent Prompt

A ready-to-use system prompt is included: `memory/SystemAgentPrompt.txt`. Use it as the system prompt for your agent at startup. It instructs the agent to read `leggenda.yaml`, manage memory via tools, and follow all workflow rules.

## Architecture

```
leggenda.yaml          ← System specification (rules, tools, format, workflow)
├── log.md             ← Short-term memory (max 3 unique days, append-only)
├── archive.md         ← Long-term memory (read-only, accessed via tools)
├── Attachment1.md     ← document 1 attached to the project
├── Attachment2.md     ← document 2 attached to the project
├── _log_tools.py      ← Log management CLI
├── _archive_tools.py  ← Archive search & extract CLI
├── _compress_tool.py  ← Compression CLI
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