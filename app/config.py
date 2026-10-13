"""Config loading. Retrieval-relevant keys feed the config hash used by caches."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "config.json"

MENU = {
    "chunk_size": [256, 512, 1024],
    "hybrid_alpha": [0.3, 0.5, 0.7],
    "rerank_depth": [10, 20, 40],
    "refusal_threshold": [round(0.2 + 0.05 * i, 2) for i in range(13)],
    "refusal_instruction": str,
}
HASH_KEYS = ["chunk_size", "hybrid_alpha", "rerank_depth", "refusal_threshold",
             "refusal_instruction", "top_k", "embed_model", "rerank_model", "llm_model"]


def load_config(path: Path | str | None = None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text())


def config_hash(cfg: dict) -> str:
    sub = {k: cfg.get(k) for k in HASH_KEYS}
    return hashlib.sha256(json.dumps(sub, sort_keys=True).encode()).hexdigest()[:12]
