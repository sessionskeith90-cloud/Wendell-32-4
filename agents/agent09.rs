use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 09 (Integrity Lattice Mapper) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Lattice integrity rules:
    // If any agent reports a status that contradicts another agent's status,
    // the lattice is broken.
    let contradictions = [
        ("OK", "ANOMALY_DETECTED"),
        ("OK", "DRIFT_DETECTED"),
        ("LOW_ENTROPY", "HIGH_ENTROPY"),
        ("TEMPORAL_ORDER_VIOLATION", "OK"),
    ];

    for (a, b) in contradictions {
        if contents.contains(a) && contents.contains(b) {
            status = "LATTICE_INTEGRITY_FAILURE";
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
        "Agent 09 (Lattice Mapper): Lattice status = {}",
        status
    ).unwrap();
}
