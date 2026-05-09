import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1].parent / "outputs" / "trace_replays"
OUT_DIR = OUT_DIR


def load_results():
    results = []
    for p in sorted(OUT_DIR.glob("C*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        results.append(data)
    return results


def heuristic_clarify_ok(turns):
    # True if assistant asked a question in any non-final turn
    for t in turns[:-1]:
        a = t.get("assistant","")
        if "?" in a or "what" in a.lower() or "which" in a.lower():
            return True
    return False


def heuristic_refine_ok(turns):
    # True if recommendations changed after a user turn that looks like a refinement
    prev = None
    for t in turns:
        recs = t.get("recommendations") or []
        names = [r.get("name") if isinstance(r, dict) else r for r in recs]
        if prev is not None and names != prev:
            return True
        prev = names
    return False


def generate_md(results):
    lines = ["# Detailed Evaluation", ""]
    lines.append("Trace | Clarify OK | Constraint handling | Refine OK | Final overlap | Turns | Notes")
    lines.append("--- | --- | --- | --- | ---: | ---: | ---")
    for r in results:
        turns = r.get("turns", [])
        clarify = "Yes" if heuristic_clarify_ok(turns) else "No"
        refine = "Yes" if heuristic_refine_ok(turns) else "No"
        overlap = f"{r['overlap']}/{r['expected_count']}"
        notes = []
        # missing expected examples
        expected = [e.lower() for e in r.get("expected",[])]
        final = [f.lower() for f in r.get("final_recommendations",[])]
        for e in expected:
            if e and e not in final:
                notes.append(f"Missed: {e}")
        if not notes:
            notes_text = ""
        else:
            notes_text = "; ".join(notes[:5])

        # constraint handling: simple heuristic if assistant returned recs and seniority was in messages
        constraint = "Partial"
        if r.get("turns"):
            # if any turn had non-empty recommendations, assume constraints handled
            any_recs = any(t.get("recommendations") for t in r.get("turns",[]))
            constraint = "Yes" if any_recs else "No"

        lines.append(f"{r['trace']} | {clarify} | {constraint} | {refine} | {overlap} | {len(turns)} | {notes_text}")

    md = "\n".join(lines)
    out = OUT_DIR / "evaluation_detailed.md"
    out.write_text(md, encoding="utf-8")
    print("Wrote detailed evaluation ->", out)


if __name__ == '__main__':
    results = load_results()
    generate_md(results)
