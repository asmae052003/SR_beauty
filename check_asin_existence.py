import json

target_asin = "B001D0OSLS"
found = False

with open("data/meta_All_Beauty_25.json", "r") as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            if data.get("asin") == target_asin:
                print(f"Found {target_asin} at line {i}")
                print(f"Image data: {data.get('image')}")
                found = True
                break
        except Exception as e:
            print(f"Error line {i}: {e}")

if not found:
    print(f"ASIN {target_asin} NOT FOUND in meta file.")
