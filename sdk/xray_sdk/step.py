import time
import uuid

# StepContext represents ONE step inside a pipeline run.
# It is designed to be used as a context manager:
#   with run.step("filter_by_price", "filter"):
#       ...
# When the step starts:
#   - start time is recorded
# When the step ends:
#   - duration is calculated
#   - step data is pushed into the parent PipelineRun

class StepContext:
    def __init__(self, run, name, step_type):
        self.run = run                      # Reference to the parent PipelineRun. This allows the step to push its data back into the run.
        self.step_id = str(uuid.uuid4())    # Unique identifier for this step. Useful for debugging and UI-level tracking.
        self.name = name                    # Human-readable step name (e.g. "fetch_competitors")
        self.step_type = step_type          # Logical type of step (e.g. "http", "filter", "llm"). This helps categorize steps in the UI or backend.
        self.start = time.time()            # Timestamp when the step started, used to calculate duration later.
        self.candidates_in = 0              # Number of items entering the step(e.g. candidates before filtering)
        self.candidates_out = 0             # Number of items exiting the step (e.g. candidates after filtering)
        self.filters = []                   # List of filters applied in this step.Each filter can record how many items it eliminated.
        self.reasoning = None               # Optional textual reasoning or notes about this step.

    def set_inputs(self, count: int):
        self.candidates_in = count          # Record how many items entered this step.Example: number of competitors before filtering.

    def set_outputs(self, count: int):
        self.candidates_out = count         # Record how many items exited this step. Example: number of competitors after filtering.

    def add_filter(self, name, eliminated):
        #  Record a filter applied during this step.

        # name:
        #    Human-readable filter name (e.g. "price_threshold")
        # eliminated:
        #    Number of items removed by this filter
        self.filters.append({
            "name": name, 
            "eliminated": eliminated
            })       

    def set_reasoning(self, text):
        self.reasoning = text           # Attach human-readable reasoning for this step.This is useful for explaining LLM decisions or heuristics.

    def finish(self):
        # Called when the step is finished.
        # Finalize the step:
        # - calculate execution duration
        # - append step data into the parent PipelineRun
        duration = (time.time() - self.start) * 1000
        # Push a structured representation of this step
        # into the parent run's step list
        self.run.steps.append({
            "step_id": self.step_id,
            "run_id": self.run.run_id,
            "step_name": self.name,
            "step_type": self.step_type,
            "candidates_in": self.candidates_in,
            "candidates_out": self.candidates_out,
            "filters_applied": self.filters,
            "reasoning": self.reasoning,
            "duration_ms": duration
        })

    def __enter__(self):  # Called automatically when entering the 'with' block.Returns the StepContext so methods like set_inputs(). can be called inside the block.
        return self

    def __exit__(self, exc_type, exc, tb):
        # Called automatically when exiting the 'with' block,
        # even if an exception occurs.

        # This guarantees that:
        # - step duration is always recorded
        # - step data is always captured
        self.finish()
