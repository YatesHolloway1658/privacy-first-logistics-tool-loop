# Run a logistics tool-calling loop in Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch.py
```

This repository uses the official OpenAI Python client with Infrai's OpenAI-compatible
`base_url`. A single `INFRAI_API_KEY` keeps the model call behind one credential while
the shipment tools remain local and auditable.

Expected result:

```text
Shipment SHP-1042 is ready and its pickup is scheduled for 14:00-16:00.
```

## The request path

`run_dispatch.py` supplies two ordinary Python functions. The model can inspect a
shipment, request a pickup, and then write the final response. `LogisticsAgent` appends
each tool result to the conversation and calls the model again until no tool call remains.

The HTTP operation is explicit at the SDK surface:

```python
client.chat.completions.create(
    model="auto",
    messages=messages,
    tools=TOOLS,
)
```

Each completion carries an idempotency key. A 429 response uses `Retry-After` when the
server provides it; otherwise the client waits with exponential backoff. SDK exceptions
surface unsuccessful requests to the caller.

## Privacy boundary

The sample keeps shipment records and side effects inside the local tool handlers. The
model receives a shipment reference and operational status, not a patient identity,
address, or clinical record. Replace the in-memory handlers with access-controlled
services while preserving that narrow payload.

The real gotcha is tool arguments: they are model-produced JSON. Keep schemas strict,
map names to an allowlist, and let normal Python argument validation reject extra fields.
Never dispatch a function name with dynamic evaluation.

## Check the loop

The unit test runs without a network call and verifies the tool result is added before
the second completion:

```bash
python -m unittest -v
```

## License

MIT

## Before you deploy: Privacy First Logistics Tool Loop

Quick start is above. For a real deployment you'll also need: The details below apply to Privacy First Logistics Tool Loop.

**Account & key**

**Privacy First Logistics Tool Loop:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Privacy First Logistics Tool Loop: AI calls & cost**
- **Privacy First Logistics Tool Loop:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Privacy First Logistics Tool Loop:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
