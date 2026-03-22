use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 12 (Harmonic Stabilizer) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Harmonic rules:
    // If too many conflicting states appear at once,
    // the system is oscillating instead of stabilizing.
    let conflict_pairs = [
        ("LOW_ENTROPY", "HIGH_ENTROPY"),
        ("DRIFT_DETECTED", "OK"),
        ("FAULT_LINE_DETECTED", "OK"),
        ("LATTICE_INTEGRITY_FAILURE", "OK"),
        ("BROKEN_PROVENANCE_CHAIN", "OK"),
    ];

    let mut conflict_count = 0;

    for (a, b) in conflict_pairs {
        if contents.contains(a) && contents.contains(b) {
            conflict_count += 1;
        }
    }

    if conflict_count >= 2 {
        status = "HARMONIC_INSTABILITY";
    }

    // Append result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 12 (Harmonic Stabilizer): Harmonic status = {}",
        status
    ).unwrap();
}
