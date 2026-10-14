---
layout: default
title: Strict LLM Memory System — study and code
description: "LLM-agnostic structured memory for agentic work. Attention-adherence study: 63% → 100% (Gemma4 26B) and 63% → 87% (Qwen3.6 35B), no fine-tuning, no RAG."
---

# Strict LLM Memory System

LLM-agnostic structured memory for agentic work — a prompt contract plus a small set of Python CLI tools. No dependencies beyond the standard library.

## Study — Attention Adherence in a Structured LLM Memory System

Legend rule adherence raised from **63% → 100%** (Gemma4 26B) and **63% → 87%** (Qwen3.6 35B), measured on a behavioural probe battery. No fine-tuning, no RAG.

- [Read the article (EN)](ARTICLE_EN.html)
- [Announcement](https://github.com/cosmok82/Strict_LLM_Memory_System/discussions/2)

## Key points

- **Progressive memory**: committed entries are never rewritten; corrections are new entries.
- **Closed tool pool**: draft → append → compression → read-only access.
- **LLM-agnostic**: any tool-calling model can drive it.

## Repository

- [Source code](https://github.com/cosmok82/Strict_LLM_Memory_System)
- [Releases](https://github.com/cosmok82/Strict_LLM_Memory_System/releases)
