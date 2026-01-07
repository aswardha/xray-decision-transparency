from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# StepSchema defines the expected structure of ONE step
# sent from the X-Ray SDK to the API.

# This schema is used for:
# - request validation
# - automatic error handling
# - guaranteeing consistent data shape

class StepSchema(BaseModel):
    step_id: str                                     # Unique identifier for the step
    run_id: str                                      # Identifier of the parent pipeline run
    step_name: str                                   # Human-readable name of the step. Example: fetch_competitors, filter_by_price
    step_type: str                                   # Logical category of the step. Example: filtering, ranking, generation
    candidates_in: int                               # Number of items entering the step
    candidates_out: int                              # Number of items exiting the step
    filters_applied: Optional[List[Dict[str, Any]]]  # Details of filters applied during the step.Optional because not all steps apply filters.
    reasoning: Optional[str]                         # Optional explanation or reasoning for this step.Commonly used for LLM or heuristic decisions.
    duration_ms: float


# RunSchema defines the expected structure of ONE complete
# pipeline execution payload.

# This is the top-level object sent by the SDK when
# PipelineRun.finish() is called.

class RunSchema(BaseModel):
    run_id: str                 # Unique identifier for the pipeline run
    pipeline_name: str          # Name of the pipeline that was executed
    context: Dict[str, Any]     # Arbitrary metadata associated with the run. Stored as a dictionary to remain flexible.
    success: bool               # Whether the pipeline completed successfully
    total_duration_ms: float    # Total execution time of the pipeline in milliseconds
    steps: List[StepSchema]     # List of all steps executed during the run


# QueryRequest defines the structure of analytical queries
# sent to the API.

# Used by the /api/v1/runs/query endpoint.

class QueryRequest(BaseModel):
    step_type: str                         # Step type to filter by. Example: "filtering"
    min_candidates_eliminated_pct: float   # Minimum percentage of candidates eliminated by the step. Example: 50 means "at least 50% eliminated".
