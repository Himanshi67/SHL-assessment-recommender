import re
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[2]
TRACES_DIR = ROOT / "GenAI_SampleConversations"
OUT_DIR = ROOT / "outputs" / "trace_replays"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "http://127.0.0.1:8000/chat"


def parse_trace_expected(path: Path):
    text = path.read_text(encoding="utf-8")
    expected = []
    for m in re.finditer(r"\|\s*\d+\s*\|\s*(.*?)\s*\|", text):
        name = m.group(1).strip()
        if name.lower() in ("name", "#"):
            continue
        expected.append(name)
    return expected


def parse_turns(path: Path):
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"### Turn\s+\d+", text)
    turns = []
    for part in parts[1:]:
        user_match = re.search(r"\*\*User\*\*[\s\S]*?>\s*(.*?)\n\n", part)
        if user_match:
            user_text = user_match.group(1).strip()
        else:
            qm = re.search(r">\s*(.*?)\n", part)
            user_text = qm.group(1).strip() if qm else ""
        turns.append(user_text)
    return turns


def run_trace(trace_path: Path):
    turns = parse_turns(trace_path)
    expected = parse_trace_expected(trace_path)

    messages = []
    last_recs = []
    for t in turns:
        messages.append({"role": "user", "content": t})
        resp = httpx.post(API_URL, json={"messages": messages}, timeout=30.0)
        data = resp.json()
        assistant = data.get("reply") or ""
        messages.append({"role": "assistant", "content": assistant})
        last_recs = [r.get("name") for r in (data.get("recommendations") or []) if isinstance(r, dict) and r.get("name")]

    # compute Recall@10
    expected_set = {e.lower() for e in expected}
    found = 0
    for r in last_recs[:10]:
        if r and r.lower() in expected_set:
            found += 1

    recall = (found / len(expected)) if expected else 0.0

    return {
        "trace": trace_path.name,
        "expected_count": len(expected),
        "found": found,
        "recall_at_10": recall,
        "returned_count": len(last_recs),
        "expected": expected,
        "returned": last_recs,
    }


def run_all():
    results = []
    trace_files = sorted(TRACES_DIR.glob("C*.md")) if TRACES_DIR.exists() else []
    for p in trace_files:
        print("Running", p.name)
        res = run_trace(p)
        results.append(res)
        out = OUT_DIR / (p.stem + ".recall.json")
        out.write_text(json.dumps(res, indent=2), encoding="utf-8")

    # mean recall
    mean = sum(r["recall_at_10"] for r in results) / len(results) if results else 0.0
    summary = {"mean_recall_at_10": mean, "per_trace": results}
    OUT_DIR.joinpath("recall_evaluation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # write human-readable report
    lines = ["# Recall@10 Evaluation", "", "Trace | Recall@10 | Found | Expected | Returned", "--- | ---: | ---: | ---: | ---:"]
    for r in results:
        lines.append(f"{r['trace']} | {r['recall_at_10']:.2f} | {r['found']} | {r['expected_count']} | {r['returned_count']}")

    lines.append("")
    lines.append(f"Mean Recall@10: {mean:.3f}")
    OUT_DIR.joinpath("recall_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote recall_report.md and recall_evaluation.json")


if __name__ == '__main__':
    run_all()
