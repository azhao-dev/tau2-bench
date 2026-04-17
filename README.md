# tau2-bench

This repository contains a local extension of `tau2-bench`, a benchmark for evaluating tool-using conversational agents in structured, task-driven domains.

The main addition in this repo is a new domain: `mobile_health`.

## What This Repo Adds

The `mobile_health` domain models operational remote patient monitoring support for home blood pressure workflows.

The first task family focuses on a realistic support problem:

- a patient upgraded to a new phone
- the clinic stopped receiving blood pressure readings
- the assistant must inspect provider-side monitoring state
- the user must repair phone/app/device state
- success is defined by final state, not by conversation style alone

In the current task set, the assistant may need to:

- verify identity
- check monitoring status
- resend monitoring consent
- issue a new pairing code
- check upload visibility
- check red-flag escalation state

The simulated user may need to:

- accept consent in the app
- grant Bluetooth permission
- pair the blood pressure monitor
- toggle Bluetooth
- take a fresh blood pressure reading
- check sync status

## Why It Fits tau2-bench

This domain follows the same core design pattern as the rest of `tau2-bench`:

- dual-control tasks, where both the assistant and the user must act
- hidden backend state and hidden user/device state
- policy-constrained tool use
- structured task files with initial state and evaluation criteria
- final success measured with environment assertions

The `mobile_health` tasks are intentionally limited to operational support and care coordination.

They do **not** cover:

- diagnosis
- medication changes
- treatment recommendations

They **do** enforce:

- identity verification before protected monitoring details
- minimum necessary access to backend information
- escalation when emergency red-flag symptoms are present

## Current Status

This repo currently includes:

- a registered `mobile_health` domain
- backend and user/device data models
- provider-side and user-side tools
- policies and support documentation
- one baseline task in `tasks_small.json`
- a larger set of variants in `tasks.json`
- focused tests for domain behavior

Full runtime testing depends on having a working native Python 3.12 environment.

## Repository Layout

Important paths:

- `src/tau2/domains/mobile_health/` — domain implementation
- `data/tau2/domains/mobile_health/` — task files, policies, and seed data
- `tests/test_domains/test_mobile_health/` — domain-specific tests
- `docs/mobile_health_domain_notes.md` — local notes for this workstream

## Running Locally

The intended flow is:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Then validate:

```bash
.venv\Scripts\python.exe -m pytest tests/test_domains/test_mobile_health -q
.venv\Scripts\python.exe -m tau2.cli check-data
```

## Summary

This repo is a simple `tau2-bench` extension centered on a new `mobile_health` domain.

Its main benchmark task is a blood pressure upload recovery workflow that requires both provider-side and patient-side actions, and it is designed to match the dual-control, state-based evaluation style of `tau2-bench`.
