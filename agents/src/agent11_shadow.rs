use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 11
    thread::sleep(Duration::from_millis(4));

    println!("Agent11-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Verify Agent 11 wrote its output
    if !contents.contains("Agent 11 (Fault-Line Detector):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory fault-line flags
    if contents.matches("FAULT_LINE_DETECTED").count() > 1 {
        status = "MULTIPLE_FAULT_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent11-Shadow: Verification status = {}",
        status
    ).unwrap();
}
