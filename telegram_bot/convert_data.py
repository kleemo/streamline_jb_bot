import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
# OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("API Key Loaded Successfully!")
else:
    print("API Key Not Found!")

# Initialize OpenAI client
client = OpenAI()
# Load the CSV file
csv_file = "telegram_bot\\dpo_ready_data.csv"
df = pd.read_csv(csv_file)
#function to fill missing non preferred response values
def get_openai_response(prompt):
    response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{"role": "user", "content": prompt}]
    )
    ai_response = response.choices[0].message.content
    return ai_response 
# Function to convert a row into the desired JSON format
def row_to_json(row):
    # Autofill non_preferred_output if missing
    rejected = row["rejected"]
    if pd.isna(rejected) or rejected == "":
        rejected = get_openai_response(row["prompt"])
        print("autfill missing value with: ",rejected)
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
                "content": rejected
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