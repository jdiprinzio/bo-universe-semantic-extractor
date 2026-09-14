---
name: github-repository-bootstrap
description: Create and initialize a new repository for GitHub Copilot Agent Mode projects. Use when starting a new AI-assisted development repository in VS Code.
---

# GitHub Repository Bootstrap Skill

## Purpose

Create a clean, specification-driven repository that is ready for GitHub Copilot Agent Mode, custom skills, MCP integrations, testing, and enterprise development.

## Primary Goal

When invoked, create or verify the following repository structure:

```text
repository-root/
│
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
│
├── .github/
│   ├── copilot-instructions.md
│   ├── prompts/
│   ├── workflows/
│   └── skills/
│
├── config/
├── docs/
├── scripts/
├── src/
├── tests/
└── output/
```

## Repository Setup Workflow

### Step 1 – Inspect

Review:

- Existing files
- Existing folders
- Existing README
- Existing Copilot instructions
- Existing workflows

Report missing items.

### Step 2 – Create Standard Folders

Create if missing:

```text
.github
.github/skills
.github/prompts
.github/workflows
config
docs
scripts
src
tests
output
```

Never delete existing folders.

### Step 3 – Create README

Generate README sections:

```markdown
# Project Name

## Purpose

## Objectives

## Architecture

## Setup

## Copilot Usage

## Security Requirements

## Repository Structure

## Development Workflow
```

### Step 4 – Create Copilot Instructions

Create:

```text
.github/copilot-instructions.md
```

Include:

- Use specification-driven development.
- Do not hardcode secrets.
- Use environment variables.
- Prefer typed models.
- Require tests.
- Preserve auditability.
- Prefer small reviewable commits.

### Step 5 – Create Environment Template

Create:

```text
.env.example
```

Populate only placeholders.

Never place actual credentials.

### Step 6 – Create Git Ignore

Ensure exclusions for:

```text
.env
.venv/
__pycache__/
output/
raw/
normalized/
*.log
```

### Step 7 – Create Python Project Files

If missing:

```text
pyproject.toml
```

Provide:

- Python 3.11+
- pytest
- ruff
- mypy

### Step 8 – Skill Installation

If a supplied skill exists:

```text
.github/skills/<skill-name>/SKILL.md
```

Verify:

- folder exists
- skill file exists
- README references the skill

Do not modify skill behavior.

### Step 9 – Validation

Confirm:

- Repository structure created
- Instructions created
- Environment template created
- Ignore file created
- Skill installed

### Step 10 – Completion Report

Return:

```text
Files Created
Files Updated
Folders Created
Missing Prerequisites
Suggested Next Prompt
```

## Initial Prompt

Use this prompt in GitHub Copilot Agent Mode:

```text
Use the github-repository-bootstrap skill.

Initialize this repository for GitHub Copilot Agent Mode development.

Create the complete repository structure, README, .env.example, .gitignore, copilot-instructions.md, configuration folders, testing folders and workflows.

Do not delete existing content.

Use specification-driven development.

Generate a completion report identifying all created files and any missing prerequisites.
```
