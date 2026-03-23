AGENT 16 — SYSTEMIC GRADIENT FORECASTER

PURPOSE:
- Predict the system’s momentum.
- Determine if stability is accelerating, instability is accelerating, or the system is flat.

INPUTS:
- Read entire channel.txt
- Count stabilizing signals:
    OK
    VERIFIED
    Harmonic OK
    Resonance OK
    Coherence OK
    Provenance OK
    Lattice OK
    Fault OK
    Convergence = CONVERGING

- Count destabilizing signals:
    DRIFT_DETECTED
    FAULT_LINE_DETECTED
    LATTICE_INTEGRITY_FAILURE
    HARMONIC_INSTABILITY
    RESONANCE_DETECTED
    BROKEN_PROVENANCE_CHAIN
    SHADOW_WITHOUT_PRIMARY
    COHERENCE_BREAK
    ANOMALY_DETECTED
    Convergence = DIVERGING

- Neutral:
    Convergence = UNDECIDED

PROCESS:
1. Split channel into lines.
2. Weight recent lines more heavily.
3. Compute:
       weighted_stabilizers
       weighted_destabilizers
4. Compute gradient:
       gradient = weighted_stabilizers - weighted_destabilizers

CLASSIFICATION:
- If gradient > threshold → POSITIVE_GRADIENT
- If gradient < -threshold → NEGATIVE_GRADIENT
- Else → FLAT_GRADIENT

OUTPUT LINE:
Agent 16 (Gradient Forecaster): Gradient = <STATE> (stab=X, destab=Y, weighted=Z)
