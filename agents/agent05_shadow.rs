use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 05 (Temporal Sequencer) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Check ordering: primaries must appear before shadows
    let ordering_rules = [
        ("Agent 01", "Agent01-Shadow"),
        ("Agent 02", "Agent02-Shadow"),
        ("Agent 03", "Agent03-Shadow"),
        ("Agent 04 (Correlator)", "Agent04-Shadow"),
    ];

    for (primary, shadow) in ordering_rules {
        let p_index = contents.find(primary);
        let s_index = contents.find(shadow);

        if let (Some(p), Some(s)) = (p_index, s_index) {
            if s < p {
                status = "TEMPORAL_ORDER_VIOLATION";
            }
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
        "Agent 05 (Sequencer): Temporal status = {}",
        status
    ).unwrap();
}
