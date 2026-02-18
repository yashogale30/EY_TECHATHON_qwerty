import json
import os

def save_agent_output(agent_name: str, data: dict):
    output_dir = "agent_outputs"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{agent_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return file_path


def load_agent_output(agent_name: str):
    file_path = os.path.join("agent_outputs", f"{agent_name}.json")
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)