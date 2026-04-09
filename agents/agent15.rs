// Updated agent15.rs

fn process_agent(agent: &mut Agent) {
    if agent.is_active() {
        // Logic for active agent
        handle_active_agent(agent);
    } else if agent.is_suspended() {
        // Logic for suspended agent
        handle_suspended_agent(agent);
    } else {
        // Logic for inactive agents
        handle_inactive_agent(agent);
    }
}

fn handle_active_agent(agent: &Agent) {
    // Implementation for active agents
    println!("Agent {} is active.", agent.id);
}

fn handle_suspended_agent(agent: &Agent) {
    // Implementation for suspended agents
    println!("Agent {} is suspended.", agent.id);
}

fn handle_inactive_agent(agent: &Agent) {
    // Implementation for inactive agents
    println!("Agent {} is inactive.", agent.id);
}