use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("Agent 07 (Entropy Divergence Scanner) is online.");

    // Read the channel
    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    // Default status
    let mut status = "OK";

    // Entropy heuristic:
    // If the same word appears too many times, entropy is low.
    // If too many unique words appear, entropy is high.
    let words: Vec<&str> = contents.split_whitespace().collect();
    let total = words.len();
    let unique = words.iter().copied().collect::<std::collections::HashSet<_>>().len();

    if total > 0 {
        let ratio = unique as f64 / total as f64;

        if ratio < 0.25 {
            status = "LOW_ENTROPY";
        } else if ratio > 0.90 {
            status = "HIGH_ENTROPY";
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
        "Agent 07 (Entropy Scanner): Entropy status = {}",
        status
    ).unwrap();
}
