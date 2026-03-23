use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 13
    thread::sleep(Duration::from_millis(4));

    println!("Agent13-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Verify Agent 13 wrote its output
    if !contents.contains("Agent 13 (Resonance Auditor):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory resonance flags
    if contents.matches("RESONANCE_DETECTED").count() > 1 {
        status = "MULTIPLE_RESONANCE_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent13-Shadow: Verification status = {}",
        status
    ).unwrap();
}

