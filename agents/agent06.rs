use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 06 (Wallet Cluster Analyzer) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Simple clustering logic:
    // If the same agent name appears more than once, flag it.
    let agents = [
        "Agent 01",
        "Agent 02",
        "Agent 03",
        "Agent 04",
        "Agent 05",
    ];

    for agent in agents {
        let count = contents.matches(agent).count();
        if count > 1 {
            status = "CLUSTER_DETECTED";
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
        "Agent 06 (Cluster Analyzer): Cluster status = {}",
        status
    ).unwrap();
}
