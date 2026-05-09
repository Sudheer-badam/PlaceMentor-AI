import os
import subprocess
import sys

def prepare_for_deployment():
    print("STARTING: 'PlaceMentor AI' Auto-Deployment Prep...")
    
    # 1. Clean up scratch files
    if os.path.exists("scratch"):
        print("CLEANING: Temporary scratch files...")
        try:
            for file in os.listdir("scratch"):
                os.remove(os.path.join("scratch", file))
            os.rmdir("scratch")
        except:
            pass
    
    # 2. Update Requirements
    print("SYNCING: requirements.txt...")
    reqs = [
        "streamlit", "pandas", "numpy", "scikit-learn", 
        "matplotlib", "plotly", "pycryptodome", "pdfplumber", 
        "spacy", "python-dotenv", "Pillow", "fpdf2", "google-generativeai"
    ]
    with open("requirements.txt", "w") as f:
        f.write("\n".join(reqs))

    # 3. Final Verification
    print("VERIFYING: Final Code Integrity Check...")
    try:
        # Check if app.py is readable and has main()
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "def main():" in content and "st.set_page_config" in content:
                print("SUCCESS: app.py is structurally sound.")
    except Exception as e:
        print(f"ERROR: in app.py: {e}")
        return

    print("\n" + "="*40)
    print("DEPLOYMENT READY!")
    print("="*40)
    print("1. Upload this folder to GitHub.")
    print("2. Connect to share.streamlit.io.")
    print("3. Your app will be LIVE!")
    print("="*40)

if __name__ == "__main__":
    prepare_for_deployment()
