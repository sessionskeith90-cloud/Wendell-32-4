AGENT 16 SHADOW — GRADIENT VERIFIER

PURPOSE:
- Ensure Agent 16’s forecast matches the evidence.
- Prevent hallucinated momentum.
- Prevent contradictions with Agent 15.

CHECKS:

1. PRIMARY OUTPUT CHECK
   - If Agent 16 line missing → MISSING_PRIMARY_OUTPUT

2. GRADIENT SANITY CHECK
   - POSITIVE_GRADIENT but destabilizers dominate → MISCLASSIFICATION
   - NEGATIVE_GRADIENT but stabilizers dominate → MISCLASSIFICATION
   - FLAT_GRADIENT but one side is overwhelming → MISCLASSIFICATION

3. ALIGNMENT WITH AGENT 15
   - If Agent 15 = CONVERGING but Agent 16 = NEGATIVE_GRADIENT → CONTRADICTORY_GRADIENT
   - If Agent 15 = DIVERGING but Agent 16 = POSITIVE_GRADIENT → CONTRADICTORY_GRADIENT

4. TREND SUFFICIENCY
   - If too few signals to compute → INSUFFICIENT_TREND_DATA

OUTPUT LINE:
Agent16-Shadow: Verification status = <STATE>
