#!/usr/bin/env python3
import json
import random
from datetime import datetime

def generate_transaction(difficulty):
    base = {
        "timestamp": datetime.now().isoformat(),
        "source": "test_harness",
        "difficulty": difficulty
    }
    if difficulty == 0:
        base["data"] = {"type": "structuring", "amounts": [random.randint(8000,9900) for _ in range(3)], "accounts": [f"acc_{random.randint(1,5)}" for _ in range(2)]}
    elif difficulty == 1:
        base["data"] = {"type": "peel_chain", "hops": random.randint(3,4), "total": random.randint(50000,100000), "mixer": random.choice([True, False])}
    elif difficulty == 2:
        base["data"] = {"type": "cross_chain", "chains": ["Ethereum","BSC","Solana"], "bridges": ["Wormhole","Multichain"], "amount": random.randint(100000,500000)}
    else:
        base["data"] = {"type": "adversarial", "pattern": "mimic_legitimate", "noise_level": random.uniform(0.5,0.9)}
    return base

tests = []
for i in range(20):
    diff = random.choices([0,1,2,3], weights=[40,30,20,10])[0]
    tests.append(generate_transaction(diff))

with open("channel.txt", "w") as f:
    for t in tests:
        f.write(json.dumps(t) + "\n")

print(f"Generated {len(tests)} test cases.")
