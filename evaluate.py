#!/usr/bin/env python3
import json

with open("channel.txt", "r") as f:
    lines = f.readlines()

test_count = 0
output_count = 0
for line in lines:
    try:
        entry = json.loads(line)
        if "difficulty" in entry:
            test_count += 1
        if "agent_output" in entry:
            output_count += 1
    except:
        pass

print(f"Test inputs: {test_count}")
print(f"Agent outputs: {output_count}")
print(f"Response ratio: {output_count/test_count:.2f}" if test_count else "No test inputs found.")
