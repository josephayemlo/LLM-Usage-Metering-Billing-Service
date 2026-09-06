INPUT_PRICE_PER_1K = 1000 # 1 input token = 1 micro-unit.
CACHED_INPUT_PRICE_PER_1K = 500 # 1 cached token = 0.5 micro-units.
OUTPUT_PRICE_PER_1K = 2000 # 1 output token = 2 micro-unit.

# This function calculates the cost in micro-units based on the number of 
# input tokens, cached input tokens, output tokens, and reasoning tokens. 
# The cost is calculated using predefined rates for input, cached input, and output tokens.
def calculate_cost_micro_units(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> int:
    if cached_input_tokens > input_tokens:
        raise ValueError("cached input tokens cannot exceed input tokens")

    uncached_input_tokens = input_tokens - cached_input_tokens

    input_cost = uncached_input_tokens * INPUT_PRICE_PER_1K // 1000

    cached_input_cost = (
        cached_input_tokens * CACHED_INPUT_PRICE_PER_1K // 1000
    )

    output_cost = (
        (output_tokens + reasoning_tokens)
        * OUTPUT_PRICE_PER_1K
        // 1000
    )

    return input_cost + cached_input_cost + output_cost

