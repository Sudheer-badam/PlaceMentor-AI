import json
import os

def inject_premium_colleges():
    output_file = "datasets/all_colleges.json"
    
    premium_colleges = [
        {"name": "LOVELY PROFESSIONAL UNIVERSITY (LPU)", "district": "PHAGWARA", "state": "Punjab", "university": "Lovely Professional University"},
        {"name": "BITS PILANI (BIRLA INSTITUTE OF TECHNOLOGY AND SCIENCE)", "district": "JHUNJHUNU", "state": "Rajasthan", "university": "BITS Pilani"},
        {"name": "MANIPAL INSTITUTE OF TECHNOLOGY (MIT)", "district": "UDUPI", "state": "Karnataka", "university": "Manipal Academy of Higher Education"},
        {"name": "VIT UNIVERSITY (VELLORE INSTITUTE OF TECHNOLOGY)", "district": "VELLORE", "state": "Tamil Nadu", "university": "VIT University"},
        {"name": "SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", "district": "KANCHIPURAM", "state": "Tamil Nadu", "university": "SRM University"},
        {"name": "CHANDIGARH UNIVERSITY", "district": "MOHALI", "state": "Punjab", "university": "Chandigarh University"},
        {"name": "AMITY UNIVERSITY", "district": "NOIDA", "state": "Uttar Pradesh", "university": "Amity University"},
        {"name": "THAPAR INSTITUTE OF ENGINEERING AND TECHNOLOGY", "district": "PATIALA", "state": "Punjab", "university": "Thapar University"},
        {"name": "CHRIST UNIVERSITY", "district": "BANGALORE", "state": "Karnataka", "university": "Christ University"},
        {"name": "REVA UNIVERSITY", "district": "BANGALORE", "state": "Karnataka", "university": "REVA University"},
        {"name": "BENNETT UNIVERSITY", "district": "GREATER NOIDA", "state": "Uttar Pradesh", "university": "Bennett University"},
        {"name": "SHIV NADAR UNIVERSITY", "district": "DADRI", "state": "Uttar Pradesh", "university": "Shiv Nadar University"}
    ]
    
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            all_colleges = json.load(f)
            
        # Add premium colleges and remove duplicates
        all_colleges.extend(premium_colleges)
        unique_colleges = list({c['name'].upper().strip(): c for c in all_colleges if c['name']}.values())
        unique_colleges.sort(key=lambda x: x['name'])
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unique_colleges, f, indent=2)
            
        print(f"Injected {len(premium_colleges)} premium colleges. New total: {len(unique_colleges)}")
    else:
        print("all_colleges.json not found.")

if __name__ == "__main__":
    inject_premium_colleges()
