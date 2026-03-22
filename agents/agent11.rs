use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 11 (Fault-Line Detector) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Fault-line rules:
    // If any two agents produce incompatible statuses,
    // or if a shadow contradicts its primary, that's a fault-line.
    let fault_pairs = [
        ("ANOMALY_DETECTED", "OK"),
        ("DRIFT_DETECTED", "OK"),
        ("LATTICE_INTEGRITY_FAILURE", "OK"),
        ("BROKEN_PROVENANCE_CHAIN", "OK"),
        ("SHADOW_WITHOUT_PRIMARY", "OK"),
    ];

    for (a, b) in fault_pairs {
        if contents.contains(a) && contents.contains(b) {
            status = "FAULT_LINE_DETECTED";
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
        "Agent 11 (Fault-Line Detector): Fault status = {}",
        status
    ).unwrap();
}
