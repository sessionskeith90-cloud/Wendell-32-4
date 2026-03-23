use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 05
    thread::sleep(Duration::from_millis(4));

    println!("Agent05-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Verify Agent 05 wrote its result
    if !contents.contains("Agent 05 (Sequencer):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory sequencing flags
    if contents.matches("TEMPORAL_ORDER_VIOLATION").count() > 1 {
        status = "MULTIPLE_SEQUENCER_FLAGS";
    }

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent05-Shadow: Verification status = {}",
        status
    ).unwrap();
}rustc agents/agent05.rs -o agent05 2>&1 | tee -a wendell_logs/agent05_build.log
