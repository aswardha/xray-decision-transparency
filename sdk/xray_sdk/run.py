import time
import uuid
import threading
import requests

# PipelineRun represents ONE execution of a pipeline.
# Think of this as a "run session".
#
# Example:
#   You start a pipeline like "competitor_selection"
#   → This class tracks:
#     - when it started
#     - what steps ran inside it
#     - how long everything took
#     - and finally reports all that data to the API

class PipelineRun:
    def __init__(self, pipeline_name, context):
        self.run_id = str(uuid.uuid4())     # Every run gets a unique ID so it can be tracked independent even if the same pipeline runs multiple times.
        self.pipeline_name = pipeline_name  # Name of the pipeline (e.g. "competitor_selection")
        self.context = context              # Arbitrary metadata about this run. Example: user_id, request_id, input parameters, etc.
        self.steps = []                     # This will hold data for each step executed in this run. Individual steps will append their data here.
        self.start = time.time()            # Timestamp when the run started, used to calculate total duration later.



       # This method is used to START a step inside the pipeline.

       # Example usage:
       #     with run.step("fetch_competitors", "http"):
       #         ...

       # It does NOT execute the step itself.
       # It returns a StepContext object that:
       # - records start time
       # - records end time
       # - captures success / failure
       # - appends step data back into self.steps

    def step(self, name, step_type):
        from .step import StepContext                # Import is done here to avoid circular imports: run.py depends on step.py,step.py also references PipelineRun
        return StepContext(self, name, step_type)    # Create and return a StepContext bound to this PipelineRun


     # Called when the entire pipeline run is finished.

     #   This:
     #   - builds a final payload containing:
     #     - run metadata
     #     - total duration
     #     - all recorded steps
     #   - sends the data asynchronously to the FastAPI backend

    def finish(self, success=True):
        payload = {                              # Build the final payload that will be sent to the API
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "context": self.context,
            "success": success,
            "total_duration_ms": (time.time() - self.start) * 1000,     # Total duration of the execution in milliseconds
            "steps": self.steps,                 # List of all step data collected during the run
        }


        # Inner function that sends the payload to the API.

        #    This is intentionally wrapped in a try/except because:
        #    - observability should NEVER break the main application
        #    - failures here should be logged, not crash the pipeline

        def send():
            try:
                requests.post(
                    "http://127.0.0.1:8000/api/v1/runs",
                    json=payload,
                    timeout=5,
                )
            except Exception as e:
                print("[XRay] Failed to send data:", e)


        # Send data in a separate thread so the main pipeline
        # does not block waiting for the API response.
        thread = threading.Thread(target=send)
        thread.start()

        # Wait briefly for the thread, but DO NOT block indefinitely.
        # This ensures:
        # - best-effort delivery
        # - low latency for the main application
        thread.join(timeout=1.0)
