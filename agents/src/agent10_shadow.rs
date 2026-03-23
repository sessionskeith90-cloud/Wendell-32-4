use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 10
    thread::sleep(Duration::from_millis(4));

    println!("Agent10-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Verify Agent 10 wrote its output
    if !contents.contains("Agent 10 (Provenance Threader):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory provenance flags
    let broken = contents.matches("BROKEN_PROVENANCE_CHAIN").count();
    let orphan = contents.matches("SHADOW_WITHOUT_PRIMARY").count();

    if broken > 0 && orphan > 0 {
        status = "CONTRADICTORY_PROVENANCE_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent10-Shadow: Verification status = {}",
        status
    ).unwrap();
}
