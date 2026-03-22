use std::fs::{self, OpenOptions};
use std::io::Write;

fn main() {
    println!("HIA (Human Interface Agent) is online.");

    let contents = fs::read_to_string("channel.txt")
        .unwrap_or_else(|_| String::from(""));

    println!("HIA saw:\n{}", contents);

    let mut file = OpenOptions::new()
        .write(true)
        .append(true)
        .open("channel.txt")
        .expect("Cannot open channel");

    writeln!(
        file,
        "HIA: Human request interpreted. Integration plan drafted."
    ).unwrap();
}
