use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 08
    thread::sleep(Duration::from_millis(4));

    println!("Agent08-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Verify Agent 08 wrote its output
    if !contents.contains("Agent 08 (Drift Sentinel):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory drift flags
    if contents.matches("DRIFT_DETECTED").count() > 1 {
        status = "MULTIPLE_DRIFT_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent08-Shadow: Verification status = {}",
        status
    ).unwrap();
}
