use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms temporal delay behind Agent 04
    thread::sleep(Duration::from_millis(4));

    println!("Agent04-Shadow is online.");

    // Read the shared channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default verification status
    let mut status = "OK";

    // Check that Agent 04 wrote its correlation result
    if !contents.contains("Agent 04 (Correlator):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Check for contradictory or malformed correlation signals
    if contents.matches("ANOMALY_DETECTED").count() > 1 {
        status = "MULTIPLE_CORRELATOR_FLAGS";
    }

    // Append verification result to channel
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent04-Shadow: Verification status = {}",
        status
    ).unwrap();
}
