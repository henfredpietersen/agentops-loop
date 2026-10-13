"""CI: runbook codes == API reason codes, and every code was raised during the test run."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.reasons import Reason  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
documented = set(re.findall(r"^### `(\w+)`", (ROOT / "RUNBOOK.md").read_text(), re.M))
api = {r.value for r in Reason}
log = ROOT / ".pytest_reasons.jsonl"
raised = {json.loads(l) for l in log.read_text().splitlines() if l.strip()} if log.exists() else set()
errors = []
if documented - api:
    errors.append(f"documented but not in API: {sorted(documented - api)}")
if api - documented:
    errors.append(f"in API but undocumented: {sorted(api - documented)}")
if api - raised:
    errors.append(f"never raised in tests: {sorted(api - raised)}")
print("\n".join(errors) or f"runbook ok: {sorted(api)}")
sys.exit(1 if errors else 0)
