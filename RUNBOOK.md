# Runbook

Every refusal carries exactly one reason code. These are the only codes the API returns
(`app/reasons.py`). CI fails if a code here is missing from the API, or if a code is never raised by the tests.

### `weak_evidence`
The best allowed span scored below `refusal_threshold`, or the model cited nothing that was retrieved and allowed.
Check: is the answer in the corpus? If yes, look at the ticket's rerank score in the trace and the retrieval mode.

### `acl_blocked`
The allowed spans were weak but a staff-only chunk would have answered. The caller is public, so the service refused.
The internal chunk's id and text never leave the retriever. Route to a staff agent.

### `injection_detected`
The guard found instructions or a role-escalation attempt in a retrieved span or in the ticket. Generation was skipped.
Find the offending doc via the retriever span's chunk ids and quarantine it with a re-ingest.

### `tool_denied`
An actor called a tool outside its allowlist (supervisor: route, refuse; specialist: search).
Treat as a model or prompt bug. Check the supervisor span's tool name.

### `budget_exceeded`
The prompt estimate was over `budget.max_prompt_tokens`. Generation was skipped. Usually a pasted document in the ticket.

### `bad_route`
The supervisor refused: not a refund, access or billing request.
