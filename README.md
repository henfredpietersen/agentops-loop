# agentops-loop

![ci](https://github.com/henfredpietersen/agentops-loop/actions/workflows/ci.yml/badge.svg)

A student-service ticket goes to a supervisor, which routes it to one specialist (refund, access or billing). The specialist answers only from a governed knowledge base, and an eval pass scores the trace. **A change counts only if it raises the mean holdout score S while staying under the cost and latency caps.** If train goes up and holdout does not, the change is dropped, and the attempt stays in the log.

**Holdout, accepted config `1a81cea6f51e`:** mean S **0.9511**, spread **0.0167** (3 samples: 0.9400, 0.9567, 0.9567). Median cost is $0.000060 per ticket, p95 latency is 1.74 ms and attack refusal is 1.0. These numbers come from the stand-in backends, see below.

| Holdout ablation | mean S | spread | recall@5 | span support | attack refusal |
|---|---|---|---|---|---|
| BM25 only | 0.9511 | 0.0167 | 1.00 | 0.81 | 1.0 |
| dense only | 0.9344 | 0.0167 | 1.00 | 0.72 | 1.0 |
| hybrid | 0.9511 | 0.0167 | 1.00 | 0.81 | 1.0 |
| hybrid + reranker | 0.9511 | 0.0167 | 1.00 | 0.81 | 1.0 |
| hybrid + reranker, **guard off** | 0.9511 | 0.0167 | 1.00 | 0.81 | **0.1** |

The corpus is only 47 chunks, so the retrieval mode barely matters: recall@5 is 1.0 everywhere. The row that moves is the guard. With it off, 9 of 10 injected pages get answered instead of refused.

**One rejected attempt, train up and holdout down** ([runs/3/decision.json](runs/3/decision.json)): lowering `refusal_threshold` from 0.5 to 0.4 raised train S from 0.8793 to 0.9136, but holdout mean S fell from 0.9511 to 0.9411. Verdict: drop. Run 5 (0.35) shows the same pattern. The train-best threshold overfits the 40 train tickets.

```bash
cp .env.example .env        # optional: add one LLM key; with no key the labelled stand-in runs
docker compose up           # API on :8080, Qdrant on :6333
```

```bash
curl -s -X POST localhost:8080/hooks/ticket -H 'content-type: application/json' \
  -d '{"ticket":"What settlement discount can staff offer on my arrears?","role":"public"}'
# HTTP 202
# {"ticket_id":"tk-9e5c4280","route":"billing","refused":true,"reason":"acl_blocked","citations":[],
#  "slack_text":"*Ticket tk-9e5c4280* | route: billing | refused (acl_blocked)\nThat information is not available to you. ...", ...}
```

### Honesty block

**Built and runnable:**
- `pip install -r requirements.txt && AGENTOPS_STANDIN=1 python -m pytest -q` runs 41 tests.
- `python -m eval.holdout` gives the 3-sample holdout report.
- `python -m eval.ablation` gives the table above.
- `python -m loop.loop` runs one improvement attempt.
- `python scripts/check_runbook.py` and `python scripts/sql_leak_check.py` are the CI checks.
- `uvicorn app.api:app --port 8080` serves the API.
- `python mcp/server.py` runs the MCP server over stdio.

**Stand-ins:**
- **The numbers above come from stand-in backends, not MiniLM and not an LLM.** The build workspace could not download HuggingFace models, so the published runs used a hashed bag-of-words embedder, an IDF-coverage reranker and a seeded extractive generator. Every report names its backend (`standin-hash|standin-idf-coverage|standin-extractive`). The MiniLM, cross-encoder and OpenAI-compatible LLM code paths are in the repo and load when models and keys are available, but they were not run for these numbers.
- Salesforce is a local fake: [agentops-connectors](https://github.com/henfredpietersen/agentops-connectors) holds the fake org, the OAuth client, the LMS/finance hooks and the n8n flow.
- Results are stored in local sqlite plus a parquet export. `bigquery/load.sql` is written but was never run against a real BigQuery project.
- Cloud Run is a manifest only, with no live deploy. The Docker image was not built in the build workspace, which had no Docker daemon.
- The price table in `config/config.json` is fixed for the cost gate, not live provider pricing.

**Not claimed:** production users, real student data, mentoring, a real Salesforce org, MiniLM or LLM-backed quality numbers.

**Disclosure:** I peeked at the holdout once at threshold 0.4 during development, before the loop existed. Nothing in the retrieval or generation logic was changed after that peek. The loop's starting threshold of 0.5 was picked because 0.4 was already the best value on train, which left the loop nothing to try.

**How it was built:** AI-assisted. Henfred Pietersen set the spec, directed the build, reviewed the output and ran the checks. The code was generated with Claude.

---

### What the tests cover

- A table always stays one chunk.
- Unchanged text keeps its chunk id across re-ingest.
- A public caller never receives an internal chunk in any retrieval mode.
- An injected page makes the service refuse, and the generator mock is never called.
- The specialist cannot call `route`, and a supervisor tool outside its allowlist gets `tool_denied`.
- Every citation was retrieved and allowed for the caller.
- Refusals spend no completion tokens.
- `budget_exceeded` fires before generation.
- Email, phone number and student id are redacted from the trace, the trace file and `slack_text`.
- A public trace contains no internal text.
- A cache hit costs about $0 and does not count toward quality scores.
- The eval pass cannot write to or read the holdout, and an `open()` spy shows it never opens it.
- The loop does not import the holdout module.
- Train up with holdout down is a drop.
- Going over the cost cap is a drop even when S rises.
- A patch that touches `eval/`, `tests/`, the splits or the runbook is rejected.
- `eval/score.py` is pinned by hash.
- Holdout and attack files match their seal.
- `/hooks/ticket` and `/ingest` return 202 with a structured body.
- OpenAPI matches the Pydantic models.
- The leaked-chunk SQL returns 0.
- Runbook codes match the API's reason codes, and every code is raised in the tests.
- MCP exposes only `search` and `refuse`, and both respect the ACL.

### Loop log

| run | change | train S | holdout mean | decision |
|---|---|---|---|---|
| 1 | threshold 0.45 | 0.8793 → 0.9014 | 0.9511 (= accepted) | drop: holdout did not rise |
| 2 | threshold 0.55 | 0.8793 → 0.8500 | not run | drop |
| 3 | threshold 0.40 | 0.8793 → 0.9136 | 0.9411 | drop: train up, holdout down |
| 4 | threshold 0.60 | 0.8793 → 0.8329 | not run | drop |
| 5 | threshold 0.35 | 0.8793 → 0.9036 | 0.9311 | drop: train up, holdout down |
| 6 | threshold 0.65 | 0.8793 → 0.8257 | not run | drop |

`sql/check.sql` holds three queries: holdout mean S by run, cost by route, and leaked-chunk count. Run them against `data/eval.db`.
