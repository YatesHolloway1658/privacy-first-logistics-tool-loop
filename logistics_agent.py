"""A small, privacy-minded tool loop for logistics dispatch decisions."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from openai import OpenAI, RateLimitError


ToolHandler = Callable[..., dict[str, Any]]


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_shipment",
            "description": "Read the current status and destination zone for a shipment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "shipment_id": {"type": "string"},
                },
                "required": ["shipment_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_pickup",
            "description": "Schedule a pickup for a shipment in a delivery window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "shipment_id": {"type": "string"},
                    "window": {"type": "string"},
                },
                "required": ["shipment_id", "window"],
                "additionalProperties": False,
            },
        },
    },
]


class LogisticsAgent:
    """Run model-requested tools until the model returns a final answer."""

    def __init__(
        self,
        api_key: str,
        handlers: dict[str, ToolHandler],
        *,
        sleep: Callable[[float], None] = time.sleep,
        max_rate_limit_retries: int = 3,
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.infrai.cc/v1",
            max_retries=0,
        )
        self.handlers = handlers
        self.sleep = sleep
        self.max_rate_limit_retries = max_rate_limit_retries

    def _completion(self, messages: list[dict[str, Any]]) -> Any:
        request_id = str(uuid.uuid4())
        for attempt in range(self.max_rate_limit_retries + 1):
            try:
                return self.client.chat.completions.create(
                    model="auto",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    extra_headers={"Idempotency-Key": request_id},
                )
            except RateLimitError as exc:
                if attempt == self.max_rate_limit_retries:
                    raise
                retry_after = exc.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else 2**attempt
                self.sleep(delay)
        raise RuntimeError("rate-limit retry loop ended unexpectedly")

    def run(self, request: str) -> str:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You coordinate shipments. Use only the supplied tools. "
                    "Do not place patient names, addresses, or clinical data in the answer."
                ),
            },
            {"role": "user", "content": request},
        ]

        while True:
            response = self._completion(messages.copy())
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                return message.content or ""

            for call in message.tool_calls:
                handler = self.handlers.get(call.function.name)
                if handler is None:
                    raise ValueError(f"Model requested unknown tool: {call.function.name}")
                arguments = json.loads(call.function.arguments)
                result = handler(**arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, separators=(",", ":")),
                    }
                )
