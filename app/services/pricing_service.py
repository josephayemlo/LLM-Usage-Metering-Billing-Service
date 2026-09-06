INPUT_PRICE_PER_1K = 1000
CACHED_INPUT_PRICE_PER_1K = 500
OUTPUT_PRICE_PER_1K = 2000

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