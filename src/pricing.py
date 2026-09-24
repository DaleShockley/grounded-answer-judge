"""Per-token prices (USD per million tokens) for cost reporting.

Anthropic first-party API rates. Thinking tokens are billed as output
tokens, and response.usage.output_tokens already includes them.
"""

PRICES = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-opus-5-5": {"input": 4.00, "output": 20.00},
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    price = PRICES[model]
    return (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000
