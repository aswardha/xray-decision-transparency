# X-Ray – Decision Transparency for Non-Deterministic Pipelines

X-Ray is a lightweight SDK and API that help developers understand why a multi-step, non-deterministic pipeline produced a particular output.

# This repository contains:
- a Python X-Ray SDK (developer instrumentation)
- a FastAPI backend (ingest + query)
- a small demo pipeline showing a real debugging scenario


For system design details, see ARCHITECTURE.md.


# Prerequisites

- Python 3.9+
- pip (or pip3)
- No external services required (uses SQLite)

Repository Structure
xray/
├── ARCHITECTURE.md      # System design & reasoning (start here)
├── README.md            # Setup & run instructions
│
├── api/                 # X-Ray backend (FastAPI)
├── sdk/                 # X-Ray SDK (developer-facing)
└── demo/                # Example pipeline

## Approach

X-Ray focuses on explaining why a pipeline produced an output, rather than what code executed.

Instead of logging raw events or storing full candidate data, the system models pipelines as a sequence of decision steps. Each step reports:
- how many candidates entered
- how many were eliminated
- what constraints or logic were applied
- optional human-readable reasoning

This enables fast diagnosis of failures in non-deterministic systems (e.g. LLM-driven selection or ranking) without blocking execution or requiring full data replay.

# Step 1: Start the X-Ray API

Open a terminal and run:

    cd api
    pip install -r requirements.txt
    uvicorn main:app --reload


You should see:

Uvicorn running on http://127.0.0.1:8000

This starts the X-Ray backend using a local SQLite database (xray.db).


# Step 2: Run the Demo Pipeline

Open a second terminal from the repo root:

Turn venv ON (activate it)
You must activate it from the repo root.

Windows PowerShell

    cd C:\Users\HP\Desktop\xray
    venv\Scripts\Activate.ps1

If PowerShell blocks it, run this once:

    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

Then retry activation.
Confirm venv is ON
You should now see:

(venv) HP@LAPTOP-... ~/Desktop/xray $


If you see (venv) → you’re good. Then do the following steps :

    cd demo
    pip install requests
    python -m demo.competitor_selection

Expected output:

Run ID: <uuid>
Run sent. Bad match simulated.

This simulates a competitor selection pipeline that:
- applies an overly strict filter
- produces a bad match
- sends step-level decision data to the X-Ray API
    
Copy the printed run_id, we’ll need it for debugging.

# Step 3: Debug the Run

The demo prints a run_id.
Use it to inspect the run.

Open in browser or via curl:

    http://localhost:8000/api/v1/debug/{run_id}


Example response:

    {
      "run_id": "...",
      "step_analysis": [
        {
          "step_name": "apply_filters",
          "reduction_rate": 98.0,
          "flags": ["HIGH_ELIMINATION"]
        }
      ]
    }

This highlights where the decision pipeline went wrong.


# Retrieve Full Run Data : 
    GET /api/v1/runs/{run_id}


Returns:
- run metadata
- all decision steps
- candidate counts
- applied filters and reasoning




# Cross-Run Query :
    POST /api/v1/runs/query


Example payload:

    {
      "step_type": "filtering",
      "min_candidates_eliminated_pct": 90
    }

Finds all runs where filtering eliminated more than 90% of candidates.



# SDK Usage

from sdk.xray_sdk import create_xray, StepType

    xray = create_xray("my_pipeline", context={"user_id": "123"})

with xray.step("filter", StepType.FILTERING) as step:

        step.set_inputs(100)
        step.set_outputs(5)
        step.set_reasoning("Strict threshold applied")
    xray.finish()

- SDK is non-blocking
- Backend failures do not affect pipeline execution


## Limitations & Future Improvements

### Current Limitations
- No deterministic replay of pipelines (by design)
- Candidate-level data is summarized, not fully stored
- No authentication or authorization
- No UI or visualization layer
- SQLite used for simplicity (not production scale)

### Future Improvements
- Correlation with distributed tracing (e.g. OpenTelemetry)
- Automatic anomaly detection on elimination rates
- Run-to-run diffing to answer “why did this fail now?”
- SDK auto-instrumentation and multi-language support
- Privacy controls and PII redaction
