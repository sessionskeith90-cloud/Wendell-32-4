
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 13 (Resonance Auditor) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Resonance rules:
    // If the same warning or error appears across multiple agents,
    // resonance is occurring.
    let resonance_signals = [
        "ANOMALY_DETECTED",
        "DRIFT_DETECTED",
        "LATTICE_INTEGRITY_FAILURE",
        "FAULT_LINE_DETECTED",
        "HARMONIC_INSTABILITY",
    ];

    for signal in resonance_signals {
        if contents.matches(signal).count() >= 3 {
            status = "RESONANCE_DETECTED";
        }
    }

    // Append result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 13 (Resonance Auditor): Resonance status = {}",
        status
    ).unwrap();
}
