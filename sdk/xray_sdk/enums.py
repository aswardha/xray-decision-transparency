from enum import Enum

# StepType defines a fixed set of allowed step categories.

# Instead of passing arbitrary strings like:
#   "filter"
#   "rank"
#   "llm"

# We use an Enum to:
# - avoid typos
# - keep step types consistent
# - make validation and UI grouping easier

class StepType(str, Enum):
    FILTERING = "filtering"         # Used for steps that remove or eliminate items. Example: filtering competitors based on price or rating
    RANKING = "ranking"             # Used for steps that reorder items. Example: ranking competitors by score or relevance
    GENERATION = "generation"       # Used for steps that generate new data. Example: LLM-generated explanations or summaries
    SELECTION = "selection"         # Used for steps that select a final subset. Example: choosing the top N candidates
