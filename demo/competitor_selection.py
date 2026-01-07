from sdk.xray_sdk import create_xray, StepType
import random


# Create a new X-Ray pipeline run.

# "competitor_selection" is the name of the pipeline.
# context contains metadata that helps identify *what* this run is about.

xray = create_xray(
    "competitor_selection",
    context={"product_id": "PHONE_CASE_123"}
)

print("Run ID:", xray.run_id)    # Print the run ID so it can be queried later via the API.

# Simulate a list of candidate competitors.
# In a real system, this could be:
# - products
# - sellers
# - recommendations

candidates = list(range(150))


# Start a step inside the pipeline.
# This step represents applying filtering logic to candidates.

# The 'with' block ensures:
# - step timing starts automatically
# - step timing ends automatically
# - telemetry is always recorded

with xray.step("apply_filters", StepType.FILTERING) as step:
    step.set_inputs(len(candidates))      # Record how many candidates entered this step

    # Simulate filtering logic.
    # Here we intentionally keep only 3 candidates out of 150
    # to demonstrate a very aggressive filter.
    filtered = random.sample(candidates, 3)
    step.add_filter("category_match", eliminated=147)     # Record which filter was applied and how many candidates it eliminated
    step.set_outputs(len(filtered))                       # Record how many candidates remain after filtering
    step.set_reasoning("Exact category match applied")    # Add human-readable reasoning explaining why the filter behaved this way


xray.finish(success=True)                       # Mark the pipeline as successfully completed. This triggers the SDK to send the full telemetry payload to the API.
print("Run sent. Bad match simulated.")         # Confirmation log for the demo script
