import subprocess
import os
import json

def download_all_states():
    base_url = "https://raw.githubusercontent.com/anburocky3/indian-colleges-data/main/data/states/"
    states = [
        "andaman-and-nicobar-islands", "andhra-pradesh", "arunachal-pradesh", "assam", "bihar",
        "chandigarh", "chhattisgarh", "dadra-and-nagar-haveli-and-daman-and-diu", "delhi", "goa",
        "gujarat", "haryana", "himachal-pradesh", "jammu-and-kashmir", "jharkhand", "karnataka",
        "kerala", "ladakh", "lakshadweep", "madhya-pradesh", "maharashtra", "manipur", "meghalaya",
        "mizoram", "nagaland", "odisha", "puducherry", "punjab", "rajasthan", "sikkim", "tamil-nadu",
        "telangana", "tripura", "uttar-pradesh", "uttarakhand", "west-bengal"
    ]
    
    target_dir = "datasets/states"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    print(f"Starting download of {len(states)} states...")
    
    for state in states:
        filename = f"{state}.json"
        target_path = os.path.join(target_dir, filename)
        url = base_url + filename
        
        print(f"Downloading {filename}...")
        try:
            # Use curl.exe for downloading
            result = subprocess.run(["curl.exe", "-L", url, "-o", target_path], capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(target_path) and os.path.getsize(target_path) > 100:
                print(f"Successfully downloaded {filename}")
            else:
                print(f"Failed to download {filename} (or file empty)")
                if os.path.exists(target_path):
                    os.remove(target_path)
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

def consolidate_all():
    target_dir = "datasets/states"
    output_file = "datasets/all_colleges.json"
    all_colleges = []
    
    if not os.path.exists(target_dir):
        print("States directory not found.")
        return
        
    files = [f for f in os.listdir(target_dir) if f.endswith(".json")]
    print(f"Consolidating {len(files)} files...")
    
    for f in files:
        file_path = os.path.join(target_dir, f)
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                for item in data:
                    name = item.get("institute_name", "").strip()
                    if name:
                        all_colleges.append({
                            "name": name,
                            "district": item.get("district", "").strip(),
                            "state": item.get("state", "").strip(),
                            "university": item.get("university", "").strip()
                        })
            except Exception as e:
                print(f"Error parsing {f}: {e}")
                
    # Unique and Sort
    unique_colleges = list({c['name']: c for c in all_colleges if c['name']}.values())
    unique_colleges.sort(key=lambda x: x['name'])
    
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(unique_colleges, out, indent=2)
        
    print(f"Total colleges consolidated: {len(unique_colleges)}")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    download_all_states()
    consolidate_all()
