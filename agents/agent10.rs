use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 10 (Provenance Threader) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Provenance rules:
    // Each agent must have:
    // 1. A primary output
    // 2. A shadow verification
    // 3. No missing or out-of-order pairs
    let pairs = [
        ("Agent 01", "Agent01-Shadow"),
        ("Agent 02", "Agent02-Shadow"),
        ("Agent 03", "Agent03-Shadow"),
        ("Agent 04", "Agent04-Shadow"),
        ("Agent 05", "Agent05-Shadow"),
        ("Agent 06", "Agent06-Shadow"),
        ("Agent 07", "Agent07-Shadow"),
        ("Agent 08", "Agent08-Shadow"),
        ("Agent 09", "Agent09-Shadow"),
    ];

    for (primary, shadow) in pairs {
        let p = contents.contains(primary);
        let s = contents.contains(shadow);

        if p && !s {
            status = "BROKEN_PROVENANCE_CHAIN";
        }
        if s && !p {
            status = "SHADOW_WITHOUT_PRIMARY";
        }
    }

    // Append result
    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "Agent 10 (Provenance Threader): Provenance status = {}",
        status
    ).unwrap();
}
