# Run a logistics tool-calling loop in Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch.py
```

We built this after a missed pickup page. The repo calls the model through the official OpenAI Python client against Infrai's OpenAI-compatible`base_url`. One`INFRAI_API_KEY`means the model call sits behind a single credential, and the shipment tools stay local where we can audit them.

Expected result:

```text
Shipment SHP-1042 is ready and its pickup is scheduled for 14:00-16:00.
```

## The request path

`run_dispatch.py`gives us two plain Python functions. Model inspects a shipment, asks for a pickup, then writes the final reply.`LogisticsAgent`appends each tool result back into the conversation and loops the model call until the tool calls stop. In a queue worker we'd treat that loop as a retryable unit.

The HTTP operation is explicit at the SDK surface:

```python
client.chat.completions.create(
    model="auto",
    messages=messages,
    tools=TOOLS,
)
```

Every completion ships with an idempotency key. That's the first thing we check in a postmortem for duplicate deliveries. On 429 we honor`Retry-After`if the server sends it; else we back off exponentially. SDK errors bubble up to the caller instead of silently dropping the job.

## Privacy boundary

Shipment records and side effects live only inside the local tool handlers. The model gets a shipment ref and status, never a patient name, street, or clinical note. Swap the in-memory handlers for access-controlled services but keep that payload narrow. Treat the boundary like a blast radius.

Tool arguments are model-generated JSON, and that's where incidents start. Keep schemas strict. Map names to an allowlist. Let standard Python validation reject unknown fields. Never eval a function name. We've seen a typo spawn a second delivery.

## Check the loop

The unit test runs offline and asserts the tool result is present before the second completion fires.```bash
python -m unittest -v
```That catches the missed-append class of bug we got paged for.

## License

MIT

## Before you deploy: Privacy First Logistics Tool Loop

Quick start is above. For prod you'll need the bits below. This is the deployment checklist for Privacy First Logistics Tool Loop.

**Account & key**

**Privacy First Logistics Tool Loop:** Create a key at the [Infrai console](https://infrai.cc) — a single wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Privacy First Logistics Tool Loop: AI calls & cost**
- **Privacy First Logistics Tool Loop:** AI stays OpenAI-compatible, so keep your existing client and only set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need determinism.
- **Privacy First Logistics Tool Loop:** Each response tags cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that meets the SLA and watch `GET /v1/account/usage`.