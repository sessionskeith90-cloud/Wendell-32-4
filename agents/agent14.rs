use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 14 (Coherence Synthesizer) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Coherence rules:
    // If too many unrelated or contradictory signals appear,
    // the system is losing coherence.
    let incoherent_pairs = [
        ("LOW_ENTROPY", "DRIFT_DETECTED"),
        ("HIGH_ENTROPY", "OK"),
        ("FAULT_LINE_DETECTED", "HARMONIC_INSTABILITY"),
        ("RESONANCE_DETECTED", "OK"),
        ("LATTICE_INTEGRITY_FAILURE", "HARMONIC_INSTABILITY"),
    ];

    let mut incoherent_count = 0;

    for (a, b) in incoherent_pairs {
        if contents.contains(a) && contents.contains(b) {
            incoherent_count += 1;
        }
    }

    if incoherent_count >= 2 {
        status = "COHERENCE_BREAK";
    }

    // Append result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 14 (Coherence Synthesizer): Coherence status = {}",
        status
    ).unwrap();
}
