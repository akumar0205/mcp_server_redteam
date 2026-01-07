# MCP Red Team PoC (Python)

> **Authorized Security Testing Only**  
> This repository contains a proof-of-concept red-teaming scanner for **MCP (Model Context Protocol) servers**. It is intended **only** for testing systems you own or have explicit permission to test.  
> A vulnerable local lab is included so the scanner can be evaluated safely.

---

## Overview

This project implements a **Python-based MCP red team scanner** that:

- Connects to MCP servers over **stdio** or **HTTP (JSON-RPC)**
- Enumerates tools, resources, and prompts
- Executes a small, deterministic vulnerability probe suite
- Captures **full transcripts** of all MCP interactions
- Produces **structured security findings** in both JSON and Markdown

The goal is not exploit automation, but **repeatable, evidence-based detection** of common MCP server security failures.

---

## What This PoC Is (and Is Not)

### ✅ This PoC **is**
- A deterministic, auditable scanner
- Focused on MCP-specific risk areas (tool abuse, SSRF, traversal, schema confusion)
- Designed to be readable and extensible
- Safe to run by default (targets only local lab infrastructure)

### ❌ This PoC **is not**
- A general penetration testing framework
- A “jailbreak” or prompt hacking tool
- Designed to scan arbitrary internet targets
- Production-ready

---

## Architecture (High Level)

