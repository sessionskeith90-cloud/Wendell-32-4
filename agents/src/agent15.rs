use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 15 (Convergence Arbiter) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "UNDECIDED";

    // Stabilizing signals
    let stabilizers = [
        "OK",
        "Verification status = OK",
        "Harmonic status = OK",
        "Resonance status = OK",
        "Coherence status = OK",
        "Provenance status = OK",
        "Lattice status = OK",
        "Fault status = OK",
    ];

    // Destabilizing signals
    let destabilizers = [
        "ANOMALY_DETECTED",
        "DRIFT_DETECTED",
        "LATTICE_INTEGRITY_FAILURE",
        "FAULT_LINE_DETECTED",
        "HARMONIC_INSTABILITY",
        "RESONANCE_DETECTED",
        "BROKEN_PROVENANCE_CHAIN",
        "SHADOW_WITHOUT_PRIMARY",
        "COHERENCE_BREAK",
        "TEMPORAL_ORDER_VIOLATION",
        "CLUSTER_DETECTED",
        "LOW_ENTROPY",
        "HIGH_ENTROPY",
    ];

    let mut stab_count = 0usize;
    let mut destab_count = 0usize;

    for s in stabilizers {
        stab_count += contents.matches(s).count();
    }

    for d in destabilizers {
        destab_count += contents.matches(d).count();
    }

    if destab_count == 0 && stab_count > 0 {
        status = "CONVERGING";
    } else if destab_count
