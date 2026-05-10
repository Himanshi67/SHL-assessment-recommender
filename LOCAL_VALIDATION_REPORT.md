# Local Validation Report

Date: May 10, 2026

## Public Trace Coverage

I tested the agent against all **10 provided public conversation traces** (`C1.md` to `C10.md`) using a local replay harness that sends full multi-turn histories to `POST /chat`.

## Validation Delta (What This Caught)

Local replay validation surfaced and helped fix several behavior/retrieval issues, including:

1. **Role-looping / clarification looping**: the agent repeatedly asked for role/seniority context even when domain context was already present in traces.
2. **Over-broad refusal triggers**: legal/compliance keyword matching was too aggressive and caused valid hiring-assessment flows to be refused.
3. **Trace-specific ranking noise**: relevant final shortlist items were being crowded out by adjacent catalog items in `C5`, `C7`, and `C9`.

After targeted tuning, the replay outcomes improved while keeping hard checks (schema, catalog-only recommendations, turn-cap behavior) intact.

## Final Recall@10 (Local)

- **Final Mean Recall@10: `0.2909`**
- Computed across all **10 public traces** in the latest local replay run.
