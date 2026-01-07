# Import the core PipelineRun class.
# This is the object that tracks an entire pipeline execution.
from .run import PipelineRun

def create_xray(pipeline_name, context=None):
    return PipelineRun(pipeline_name, context or {})

 
    # Factory function to create a new PipelineRun instance.

    # This function exists to provide a clean, simple public API
    # for users of the X-Ray SDK.

    # Instead of doing this:
    #     run = PipelineRun("competitor_selection", {...})

    # Users do this:
    #     run = create_xray("competitor_selection", {...})

    # This hides internal implementation details and makes the SDK
    # easier to evolve in the future.
    

    # If no context is provided, default to an empty dictionary.
    # Context typically contains metadata like:
    # - request_id
    # - user_id
    # - input parameters