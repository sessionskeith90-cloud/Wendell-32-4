use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms behind Agent 09
    thread::sleep(Duration::from_millis(4));

    println!("Agent09-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    // Verify Agent 09 wrote its output
    if !contents.contains("Agent 09 (Lattice Mapper):") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Detect contradictory lattice flags
    if contents.matches("LATTICE_INTEGRITY_FAILURE").count() > 1 {
        status = "MULTIPLE_LATTICE_FLAGS";
    }

    // Append verification result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent09-Shadow: Verification status = {}",
        status
    ).unwrap();
}
