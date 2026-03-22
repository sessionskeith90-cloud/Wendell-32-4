use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 01 (Diagnostics) is online.");

    let contents = fs::read_to_string("channel.txt")
        .expect("Cannot read channel");

    println!("Agent 01 read: {}", contents);

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 01 (Diagnostics): Systems nominal. No internal faults detected."
    ).unwrap();
}

