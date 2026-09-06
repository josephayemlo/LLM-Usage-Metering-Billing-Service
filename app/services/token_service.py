def calculate_billable_tokens(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int,
) -> int:
    uncached_input_tokens = input_tokens - cached_input_tokens

    billable_output_tokens = output_tokens + reasoning_tokens

    return uncached_input_tokens + cached_input_tokens + billable_output_tokens