import json

with open("C:\\Users\\lilia\\Documents\\streamline_jb_bot\\telegram_bot\\training_data.json", "r", encoding="utf-8") as infile:
    data = json.load(infile)

with open("output.jsonl", "w", encoding="utf-8") as outfile:
    for obj in data:
        json.dump(obj, outfile)
        outfile.write("\n")
