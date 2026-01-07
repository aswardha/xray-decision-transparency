def elimination_rate(step):
    
    # Calculate how aggressively a step reduces candidates.

    # Elimination rate answers the question:
    # "What fraction of inputs were removed by this step?"

    # Formula:
    #     (candidates_in - candidates_out) / candidates_in

    # Example:
    #     candidates_in = 100
    #     candidates_out = 40
    #     elimination_rate = 0.6 (60% eliminated)

    # This metric is used for:
    # - querying suspicious steps
    # - debugging pipeline behavior
    # - identifying overly aggressive filters
    

    # Guard against division by zero.
    # If a step received no inputs, it cannot eliminate anything.
    if step.candidates_in == 0:
        return 0.0

    # Calculate the elimination ratio.
    return (step.candidates_in - step.candidates_out) / step.candidates_in
