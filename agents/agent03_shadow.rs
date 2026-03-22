use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms temporal delay behind primary
    thread::sleep(Duration::from_millis(4));

    println!("Agent03-Shadow is online.");

    // Read the shared channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Basic verification: did Agent 03 write anything?
    let mut status = "OK";

    if !contents.contains("Agent 03") {
        status = "MISSING_PRIMARY_OUTPUT";
    }

    // Append verification result to channel
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent03-Shadow: Verification status = {}",
        status
    ).unwrap();
}

