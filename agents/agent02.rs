use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 02 is online.");

    // Read the shared channel
    let contents = fs::read_to_string("channel.txt")
        .expect("Cannot read channel");

    println!("Agent 02 received: {}", contents);

    // Write a response
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(file, "Agent 02: Monitoring complete. No anomalies detected.").unwrap();
}
