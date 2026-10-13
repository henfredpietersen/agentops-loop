"""Tokenizer shared by BM25, the stand-in embedder and the stand-in reranker."""
import math
import re
from collections import Counter

STOP = set("""a an the and or of to in on for is are was were be been it its this that i my me we you your
do does did can could would should will with at by from as how what when where which who why if not no
have has had am so up out there their they them our us about into than then just any all get got""".split())


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def idf_table(docs: list[list[str]]) -> dict[str, float]:
    n = len(docs) or 1
    df = Counter(t for d in docs for t in set(d))
    return {t: math.log(1 + n / c) for t, c in df.items()}
