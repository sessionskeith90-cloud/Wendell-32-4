use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 07
    thread::sleep(Duration::from_millis(4));

    println!("Agent07-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Verify Agent 07 wrote its output
    if !contents.contains("Agent 07 (Entropy Scanner):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory entropy flags
    let low = contents.matches("LOW_ENTROPY").count();
    let high = contents.matches("HIGH_ENTROPY").count();

    if low > 0 && high > 0 {
        status = "CONTRADICTORY_ENTROPY_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent07-Shadow: Verification status = {}",
        status
    ).unwrap();
}
