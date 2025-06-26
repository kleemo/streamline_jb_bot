import json
import pandas as pd

# Load the CSV file
csv_file = "telegram_bot/dpo_ready_data.csv"
df = pd.read_csv(csv_file)

# Function to convert a row into the desired JSON format
def row_to_json(row):
    return {
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": row["prompt"]
                }
            ],
            "tools": [],
            "parallel_tool_calls": True
        },
        "preferred_output": [
            {
                "role": "assistant",
                "content": row["chosen"]
            }
        ],
        "non_preferred_output": [
            {
                "role": "assistant",
                "content": row["rejected"]
            }
        ]
    }

# Convert each row and write to JSONL
jsonl_file = "telegram_bot\\structured_dpo_data.jsonl"
with open(jsonl_file, "w", encoding="utf-8") as f:
    for _, row in df.iterrows():
        json.dump(row_to_json(row), f, ensure_ascii=False)
        f.write("\n")

print(f"Successfully created {jsonl_file}")