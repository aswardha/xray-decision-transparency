# X-Ray Architecture

# Overview

X-Ray is a decision-transparency system for multi-step, non-deterministic pipelines (e.g. LLM-driven selection, ranking, categorization).
Traditional tracing explains what executed. X-Ray explains why a particular output was chosen in non-deterministic pipelines.
The system is intentionally designed to prioritize debuggability and reasoning visibility over deterministic replay or full data capture.

# System Design

# High-Level Flow

 User Pipeline

      └─ X-Ray SDK (in-process, non-blocking)
   
        └─ PipelineRun (in-memory)
   
              └─ async send on finish()
              
                    └─ X-Ray API
                    
                          └─ Storage (metadata + step metrics)


# Design constraint:
X-Ray must never block or alter pipeline behavior. Loss of observability is acceptable; loss of correctness is not.

# Core Data Model
# PipelineRun

Represents one execution of a pipeline.

PipelineRun
- run_id
- pipeline_name
- context (JSON)
- success
- total_duration_ms


The context field is intentionally schema-less. Different pipelines require different identifiers (e.g. product_id, listing_id, user_id). Enforcing a fixed schema would tightly couple the SDK to specific domains and reduce adoption.

# StepContext (Core Abstraction)

Represents a decision step, not just a function call.

StepContext
- step_id
- run_id
- step_name
- step_type (FILTERING, RANKING, GENERATION, SELECTION)
- candidates_in
- candidates_out
- filters_applied (optional)
- reasoning (free text)
- duration_ms


Each step captures:
- what came in
- what went out
- what logic reduced or transformed candidates
- why that logic was applied


# Data Model Rationale
# Why step-centric instead of event-centric?

Logs and spans record events. They do not capture decision intent.
X-Ray models decision steps because most debugging questions are about why candidates were eliminated or chosen, not which function executed.

Alternative considered: raw structured logs
Rejected because: reconstructing decision intent post-hoc is brittle and expensive.


# Why counts + summaries instead of full candidate storage?

Every step must report:
- candidates_in
- candidates_out

Candidate-level details are optional and sampled.

Alternative considered: storing every candidate and rejection reason
Rejected because:
5,000 candidates × multiple steps becomes prohibitively expensive.
Teams stop instrumenting when observability is too costly.

The system optimizes for diagnosis, not replay.


# Why filters are first-class?

In practice, most failures come from over-aggressive constraints.
Logging “a filter ran” is insufficient. X-Ray requires filters to report how many candidates they eliminated, making problematic logic immediately visible.

# Debugging Walkthrough

Scenario: A competitor selection pipeline matches a phone case to a laptop stand.

# Step 1: Inspect the run

Query the run:
    
    GET /api/v1/runs/{run_id}


You see:
    - keyword generation produced generic terms ("laptop", "stand")
    - filtering reduced candidates from 150 → 3
    - category filter eliminated the majority of candidates

# Step 2: Identify the failure point

The filtering step shows a ~98% elimination rate, far higher than baseline.
This immediately narrows investigation to constraint logic, not retrieval or ranking.


# Step 3: Validate across runs

    POST /api/v1/runs/query
    {
     "step_type": "filtering",
     "min_candidates_eliminated_pct": 90
    }

Result: the same category filter eliminates > 90% of candidates in a large percentage of runs.
Root cause: category matching is too strict (exact match instead of hierarchical).
This diagnosis does not require replaying the pipeline or inspecting raw logs - only step-level decision data.


# Queryability Across Pipelines

X-Ray is used across heterogeneous pipelines with different steps.
Queryability is enabled through conventions, not hard-coded schemas.

# Enforced Conventions
- Standard step types (FILTERING, RANKING, etc.)
- Mandatory candidate counts for every step
- Free-form but meaningful reasoning text
- Schema-less run context

This enables queries like:
    “Show all runs where a filtering step eliminated >90% of candidates” without knowing pipeline-specific details.

# Trade-off:
Developers must follow light conventions. This constraint enables powerful cross-pipeline analysis that would otherwise be impossible.

# Performance & Scale
# The 5,000 → 30 Candidate Case

Capturing full details for all candidates is often unnecessary and expensive.

X-Ray supports capture levels:
- Minimal: counts only
- Summary: aggregated stats
- Detailed: representative samples
- Full: explicit opt-in

# Key trade-off:
X-Ray does not support deterministic replay. In non-deterministic systems (LLMs, external APIs), replay often gives a false sense of correctness while significantly increasing cost.


# Developer Experience
# Minimal Instrumentation

xray = create_xray("pipeline", context={...})
result = pipeline(input)
xray.finish()


Provides:
    run-level visibility,
    success/failure,
    duration.

Full Instrumentation with xray.step("filter", StepType.FILTERING) as step:

    step.set_inputs(count)
    ...
    step.set_outputs(count)

Instrumentation is incremental. Teams can add depth where debugging value is highest.


# Backend Unavailability

The SDK never blocks execution.
- network failure → warning only
- API down → data dropped
- pipeline correctness unaffected

Observability must not affect system behavior.


# Real-World Application

In a previous recommendation system (retrieve → score → re-rank → diversify → select), failures surfaced as “stale results” with no clear cause.

X-Ray-style instrumentation at the filtering and diversification stages would have immediately revealed that a diversity constraint was eliminating most fresh content for high-activity users - an issue that previously required days of log analysis and hypothesis testing.

# API Summary

POST /api/v1/runs          Ingest a pipeline run

GET  /api/v1/runs/{id}     Retrieve a run and its steps

POST /api/v1/runs/query    Cross-run analytical queries

GET  /api/v1/debug/{id}    Debug-focused analysis view


The API surface is intentionally small. Most complexity lives in the data model and conventions, not endpoint count.


# What’s Next
If shipped for real-world use:
- correlation with distributed tracing (OpenTelemetry)
- anomaly detection on elimination rates
- run-to-run diffing for “why did this fail?”
- SDK auto-instrumentation and multi-language support
- privacy controls and PII redaction


# Final Note

X-Ray intentionally trades completeness for practical debuggability.
The system is opinionated because ambiguity is the primary enemy when debugging non-deterministic pipelines.
