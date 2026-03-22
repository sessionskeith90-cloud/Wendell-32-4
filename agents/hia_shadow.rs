use std::{thread, time::Duration};
use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    // 4ms temporal delay
    thread::sleep(Duration::from_millis(4));

    println!("HIA-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    if !contents.contains("HIA:") {
        status = "MISSING_HIA_OUTPUT";
    }

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "HIA-Shadow: Verification status = {}",
        status
    ).unwrap();
}
