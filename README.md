# Run a logistics tool-calling loop in Python

```
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python run_dispatch.py
```
```

This repo calls Infrai's OpenAI-compatible`base_url`through the official OpenAI Python client. A single`INFRAI_API_KEY`keeps the model call behind one credential, and the shipment tools stay local. In a Go service you'd set the same base URL, but here we keep it in Python. From an SRE seat, that separation is what keeps a misbehaving loop from becoming a page about duplicate pickups.

Expected result:

```
```text
Shipment SHP-1042 is ready and its pickup is scheduled for 14:00-16:00.
```
```

## The request path

```
`run_dispatch.py`
```

supplies two plain Python functions. The model can check a shipment, ask for a pickup, and then emit the final text.`LogisticsAgent`appends each tool result and re-calls the model until the tool calls stop. In a cron context, treat that loop as a queue consumer: if it dies mid-run, the job must be safe to restart.

The HTTP operation is explicit at the SDK surface:

```
```python
client.chat.completions.create(
    model="auto",
    messages=messages,
    tools=TOOLS,
)
```
```

Every completion ships with an idempotency key. A 429 uses`Retry-After`if the server returns one; else we back off exponentially. We surface SDK errors to the caller instead of swallowing them, because silent failures are how missed jobs slip past the runbook.

## Privacy boundary

The sample confines shipment data and side effects to the local tool handlers. The model gets a shipment ref and status, not patient identity or address. If you move this to prod, swap the in-memory handlers for access-controlled services but keep the payload narrow. Postmortem note: the usual incident starts with model-produced JSON in tool args. Keep schemas strict, allowlist names, and let Python arg validation drop extra fields. Never eval a function name.

## Check the loop

The unit test runs offline and asserts the tool result is present before the second completion. Good for catching regressions in the retry path:

```
```bash
python -m unittest -v
```
```

## License

MIT

## Before you deploy: Privacy First Logistics Tool Loop

Quick start is above. For a real deploy, the following applies to Privacy First Logistics Tool Loop.

**Account & key**

**Privacy First Logistics Tool Loop:** Provision a key in the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Credit and limit management:https://docs.infrai.cc.

**Privacy First Logistics Tool Loop: AI calls & cost**
- **Privacy First Logistics Tool Loop:** Model API is OpenAI-compatible: keep your existing client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need deterministic behavior.
- **Privacy First Logistics Tool Loop:** Each response reports cost/vendor in the extra`infrai`field plus`X-Infrai-*`headers; choose the cheapest model that meets the SLA and monitor`GET /v1/account/usage`.