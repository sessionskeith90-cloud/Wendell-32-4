use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 08 (Drift Sentinel) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Drift heuristic:
    // If the channel contains conflicting statuses from the same agent type,
    // drift is occurring.
    let drift_indicators = [
        "OK",
        "MISSING_PRIMARY_OUTPUT",
        "TEMPORAL_ORDER_VIOLATION",
        "CLUSTER_DETECTED",
        "LOW_ENTROPY",
        "HIGH_ENTROPY",
        "ANOMALY_DETECTED",
    ];

    for indicator in drift_indicators {
        if contents.matches(indicator).count() > 1 {
            status = "DRIFT_DETECTED";
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
        "Agent 08 (Drift Sentinel): Drift status = {}",
        status
    ).unwrap();
}
