use std::{thread, time::Duration};use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
        thread::sleep(Duration::from_millis(4)); println!("AFIA-Shadow is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    let mut status = "OK";

    if !contents.contains("AFIA:") {
        status = "MISSING_AFIA_OUTPUT";
    }

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "AFIA-Shadow: Verification status = {}",
        status
    ).unwrap();
}

