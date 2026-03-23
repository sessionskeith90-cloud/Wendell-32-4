use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 14
    thread::sleep(Duration::from_millis(4));

    println!("Agent14-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|| String::from(""));

    let mut status = "OK";

    // Verify Agent 14 wrote its output
    if !contents.contains("Agent 14 (Coherence Synthesizer):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory coherence flags
    if contents.matches("COHERENCE_BREAK").count() > 1 {
        status = "MULTIPLE_COHERENCE_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent14-Shadow: Verification status = {}",
        status
    ).unwrap();
}
