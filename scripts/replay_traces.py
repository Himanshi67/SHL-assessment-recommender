import os
import re
import json
import httpx
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
TRACES_DIR = ROOT / "GenAI_SampleConversations"
OUTPUT_DIR = ROOT / "outputs" / "trace_replays"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "http://localhost:8000/chat"


def parse_trace(path: Path):
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"### Turn\s+\d+", text)
    turns = []
    # first part is header
    for part in parts[1:]:
        # find user block (lines starting with > after **User**)
        user_match = re.search(r"\*\*User\*\*[\s\S]*?>\s*(.*?)\n\n", part)
        if user_match:
            user_text = user_match.group(1).strip()
        else:
            # fallback: first quoted block
            qm = re.search(r">\s*(.*?)\n", part)
            user_text = qm.group(1).strip() if qm else ""

        turns.append({"user": user_text, "agent_block": part})

    # extract expected shortlist from whole file (table rows)
    expected = []
    for m in re.finditer(r"\|\s*\d+\s*\|\s*(.*?)\s*\|", text):
        name = m.group(1).strip()
        # ignore header rows like 'Name'
        if name.lower() in ("name", "#"):
            continue
        expected.append(name)

    return turns, expected


def replay_trace(trace_path: Path):
    turns, expected = parse_trace(trace_path)
    messages = []
    logs = []

    for i, t in enumerate(turns, start=1):
        user_msg = t["user"]
        messages.append({"role": "user", "content": user_msg})

        payload = {"messages": messages}
        try:
            resp = httpx.post(API_URL, json=payload, timeout=30.0)
        except Exception as e:
            print(f"ERROR calling API for {trace_path.name} turn {i}: {e}")
            return None

        if resp.status_code != 200:
            print(f"ERROR calling API for {trace_path.name} turn {i}: {resp.status_code} {resp.text}")
            return None

        data = resp.json()

        # record assistant reply
        assistant_content = data.get("reply") or ""
        messages.append({"role": "assistant", "content": assistant_content})

        log_entry = {
            "turn": i,
            "user": user_msg,
            "assistant": assistant_content,
            "recommendations": data.get("recommendations"),
            "end_of_conversation": data.get("end_of_conversation"),
        }
        logs.append(log_entry)

        # If the API signalled end_of_conversation True, still continue to record but
        # do not stop replay — we want to run through the trace turns for diagnostics.

    # compute final overlap
    final_recs = []
    if logs:
        last = logs[-1]
        recs = last.get("recommendations") or []
        final_recs = [r.get("name") for r in recs if isinstance(r, dict) and r.get("name")]

    overlap = 0
    expected_set = {e.lower() for e in expected}
    for r in final_recs:
        if r and r.lower() in expected_set:
            overlap += 1

    result = {
        "trace": trace_path.name,
        "expected": expected,
        "final_recommendations": final_recs,
        "overlap": overlap,
        "expected_count": len(expected),
        "turns": logs,
    }

    out_file = OUTPUT_DIR / (trace_path.stem + ".json")
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote replay for {trace_path.name} -> {out_file}")
    return result


def run_all():
    results = []
    trace_files = sorted(TRACES_DIR.glob("C*.md")) if TRACES_DIR.exists() else []
    if not trace_files:
        print(f"No trace files found in {TRACES_DIR}")
    for p in trace_files:
        print("Replaying", p.name)
        res = replay_trace(p)
        if res:
            results.append(res)

    # write summary markdown
    md_lines = ["# Replay Evaluation", "", "Trace | Overlap | Expected | Returned | Turns", "--- | ---: | --- | --- | ---"]
    for r in results:
        md_lines.append(
            f"{r['trace']} | {r['overlap']}/{r['expected_count']} | {r['expected_count']} | {len(r['final_recommendations'])} | {len(r['turns'])}"
        )

    md = "\n".join(md_lines)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    md_path = OUTPUT_DIR / f"evaluation_{timestamp}.md"
    md_path.write_text(md, encoding="utf-8")
    print("Wrote summary ->", md_path)


if __name__ == "__main__":
    run_all()
