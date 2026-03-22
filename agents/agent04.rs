use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 04 (Anomaly Correlator) is online.");

    // Read the entire channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Correlation logic:
    // If any shadow reports a mismatch or missing output, escalate.
    if contents.contains("MISSING_PRIMARY_OUTPUT")
        || contents.contains("verification failed")
        || contents.contains("SHADOW_MISMATCH")
        || contents.contains("FAULT")
        || contents.contains("ERROR")
    {
        status = "ANOMALY_DETECTED";
    }

    // Append correlation result to channel
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 04 (Correlator): Correlation status = {}",
        status
    ).unwrap();
}
