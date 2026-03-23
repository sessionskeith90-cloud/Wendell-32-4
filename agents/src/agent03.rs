use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 03 (Logic Engine) is online.");

    let contents = fs::read_to_string("channel.txt")
        .expect("Cannot read channel");

    println!("Agent 03 scanned: {}", contents);

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    // Simple conditional logic
    if contents.contains("fault") || contents.contains("error") {
        writeln!(
            file,
            "Agent 03 (Logic Engine): Alert — potential fault detected in system messages."
        ).unwrap();
    } else {
        writeln!(
            file,
            "Agent 03 (Logic Engine): All systems appear stable based on current data."
        ).unwrap();
    }
}

