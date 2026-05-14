import streamlit as st
import os
import sys
import base64
import random
import string
import time
import datetime

# Use bundled external_libs only on Windows local environments (to handle user's disk space issues)
# On Streamlit Cloud (Linux), we MUST use the native environment.
if os.name == 'nt':
    _ext_libs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "win_libs_do_not_push")
    if _ext_libs not in sys.path:
        sys.path.insert(0, _ext_libs)
from database.db_manager import (
    init_db, register_user, login_user, save_quiz_score, 
    get_user_scores, save_skill, get_user_skills, 
    save_coding_progress, get_coding_stats, get_community_stats,
    get_security_question, reset_password, post_notice, get_notices,
    delete_notice, send_feedback, get_all_feedback, get_all_user_stats,
    get_security_logs, delete_user, update_user_status
)
from utils.ml_model import train_model
from utils.platform_sync import sync_leetcode_stats, sync_harkerrank_stats
from utils.quiz_data import QUIZ_DATA
from utils.social_sync import fetch_klu_live_notices
import plotly.graph_objects as go
from fpdf import FPDF
import io
import urllib.parse
import json

# Load College Data
def load_college_data():
    try:
        with open("datasets/all_colleges.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return [{"name": "KL UNIVERSITY", "state": "Andhra Pradesh"}]

COLLEGE_LIST = load_college_data()
COLLEGE_NAMES = [c["name"] for c in COLLEGE_LIST]

# Page Configuration
st.set_page_config(
    page_title="PlaceMentor AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cached Asset Loader
@st.cache_data
def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        return ""
    return ""

@st.cache_data
def get_css_content(css_path):
    try:
        if os.path.exists(css_path):
            with open(css_path) as f:
                return f.read()
    except:
        return ""
    return ""

def load_css():
    st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;800;900&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    bg_path = os.path.join(base_path, "assets", "futuristic_bg.png")
    style_path = os.path.join(base_path, "assets", "style.css")

    bg_data = get_base64_image(bg_path)
    if bg_data:
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("data:image/png;base64,{bg_data}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)

    style_content = get_css_content(style_path)
    if style_content:
        st.markdown(f"<style>{style_content}</style>", unsafe_allow_html=True)

load_css()

def generate_certificate(name, university, score, date):
    from fpdf import FPDF
    # Using fpdf2 for better features if available, but FPDF is in requirements
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    
    # --- PATRIOTIC TRICOLOR BORDER ---
    # Saffron
    pdf.set_draw_color(255, 153, 51)
    pdf.set_line_width(5)
    pdf.rect(5, 5, 287, 200)
    
    # White (Inner)
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(2)
    pdf.rect(8, 8, 281, 194)
    
    # Green (Innermost)
    pdf.set_draw_color(19, 136, 8)
    pdf.set_line_width(3)
    pdf.rect(10, 10, 277, 190)

    # --- BACKGROUND DECORATION ---
    pdf.set_font("Helvetica", "B", 100)
    pdf.set_text_color(240, 240, 240)
    pdf.text(40, 120, "CERTIFIED")

    # --- HEADER ---
    pdf.set_font("Helvetica", "B", 45)
    pdf.set_text_color(45, 52, 54) # Dark Grey
    pdf.ln(20)
    pdf.cell(0, 30, "PLACEMENT READINESS CERTIFICATE", ln=True, align="C")
    
    # Subtitle
    pdf.set_font("Helvetica", "I", 15)
    pdf.set_text_color(108, 92, 231) # Purple
    pdf.cell(0, 10, "OFFICIALLY VERIFIED BY PLACEMENTOR AI NEURAL ENGINE", ln=True, align="C")
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "This prestigious certificate is awarded to", ln=True, align="C")
    
    # --- NAME ---
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 40)
    pdf.set_text_color(214, 48, 49) # Reddish/Deep Pink
    pdf.cell(0, 25, name.upper(), ln=True, align="C")
    
    # --- DESCRIPTION ---
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(45, 52, 54)
    pdf.multi_cell(0, 10, f"In recognition of outstanding performance and career preparation at {university}.\nThe candidate has achieved a verified placement readiness score of:", align="C")
    
    # --- SCORE ---
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 35)
    pdf.set_text_color(0, 184, 148) # Emerald Green
    pdf.cell(0, 20, f"{score}%", ln=True, align="C")
    
    # --- FOOTER ---
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(99, 110, 114)
    
    # Digital Signatures
    pdf.cell(100, 10, "__________________________", ln=0, align="C")
    pdf.cell(0, 10, "__________________________", ln=1, align="C")
    pdf.cell(100, 10, "DR. AI ALGORITHM", ln=0, align="C")
    pdf.cell(0, 10, "PLACEMENT DIRECTOR", ln=1, align="C")
    
    # Date and Verification
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, f"Issued on: {date} | Unique ID: PM-{random.randint(100000, 999999)}", ln=True, align="C")
    
    # --- OFFICIAL SEAL ---
    # Ashoka Chakra Inspired Seal
    pdf.set_draw_color(0, 0, 128) # Navy Blue
    pdf.set_line_width(1)
    pdf.ellipse(135, 175, 25, 25, 'D')
    pdf.set_font("Helvetica", "B", 6)
    pdf.text(138, 188, "BHARAT AI VERIFIED")
    
    return pdf.output()

def auto_sync_notices():
    """Background task to sync KLU notices once every 24 hours."""
    try:
        from datetime import datetime, timedelta
        # Get latest notices from DB
        notices = get_notices()
        
        should_sync = False
        if not notices:
            should_sync = True
        else:
            # notices[0][2] is the date string from DB: "YYYY-MM-DD HH:MM:SS"
            last_date_str = notices[0][2]
            try:
                # Handle potential format variations
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d %H:%M:%S")
                # Sync if more than 24 hours have passed since the last notice
                if (datetime.now() - last_date) > timedelta(hours=24):
                    should_sync = True
            except:
                should_sync = True
        
        if should_sync:
            live_data = fetch_klu_live_notices()
            if live_data:
                existing_contents = [n[1] for n in notices]
                for item in live_data:
                    if item['content'] not in existing_contents:
                        post_notice(item['content'])
    except Exception as e:
        # Fail silently to avoid interrupting the user experience
        pass

# Initialize Database and Models
if 'db_initialized' not in st.session_state:
    init_db()
    # Only train if model doesn't exist to speed up startup
    if not os.path.exists("models/placement_model.pkl"):
        train_model()
    st.session_state.db_initialized = True

def generate_captcha():
    """Generates a random 6-character alphanumeric CAPTCHA with mixed case."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'captcha' not in st.session_state:
        st.session_state.captcha = generate_captcha()
    if 'otp_sent' not in st.session_state:
        st.session_state.otp_sent = False
    if 'generated_otp' not in st.session_state:
        st.session_state.generated_otp = None
    if 'temp_user' not in st.session_state:
        st.session_state.temp_user = None
    if 'auth_view' not in st.session_state:
        st.session_state.auth_view = "landing"
    
    # Daily Auto-Sync for KLU Official Updates (Triggered once per session)
    if 'last_auto_sync' not in st.session_state:
        auto_sync_notices()
        st.session_state.last_auto_sync = time.time()

    if st.session_state.logged_in:
        # High-Visibility Patriotic Watermark (Solid Tricolor)
        import urllib.parse
        info = st.session_state.get('watermark_info', '').split(' - ')
        uni = info[0] if len(info) > 0 else "PlaceMentor AI"
        roll = info[1] if len(info) > 1 else "Student"
        user_name = st.session_state.user.get('username', 'User')
        
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600">
            <text x="50%" y="45%" transform="rotate(-45 300 300)" 
                  fill="rgba(255, 153, 51, 0.2)" font-family="Orbitron, sans-serif" 
                  font-size="22" font-weight="bold" text-anchor="middle" dominant-baseline="middle">
                {uni}
            </text>
            <text x="50%" y="50%" transform="rotate(-45 300 300)" 
                  fill="rgba(255, 255, 255, 0.25)" font-family="Orbitron, sans-serif" 
                  font-size="20" font-weight="bold" text-anchor="middle" dominant-baseline="middle">
                {user_name} [{roll}]
            </text>
            <text x="50%" y="55%" transform="rotate(-45 300 300)" 
                  fill="rgba(51, 255, 51, 0.35)" font-family="Orbitron, sans-serif" 
                  font-size="14" font-weight="bold" text-anchor="middle" dominant-baseline="middle">
                🇮🇳 BHARAT AI VERIFIED 🇮🇳
            </text>
        </svg>"""
        svg_encoded = urllib.parse.quote(svg)
        st.markdown(f"""
        <style>
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 99999;
            background-image: url('data:image/svg+xml;utf8,{svg_encoded}');
            background-repeat: repeat;
        }}
        </style>
        """, unsafe_allow_html=True)
        sidebar_nav()
    else:
        auth_page()

def auth_page():
    # Top Section: Neon Title and Futuristic Subtitle
    st.markdown('<h1 class="neon-title">PLACEMENTOR AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title" style="text-align: left; padding-left: 5%; background: linear-gradient(90deg, #ff00cc, #3333ff, #00f2fe, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold; letter-spacing: 4px; margin-bottom: 30px;">THE ULTIMATE CAREER INTELLIGENCE SYSTEM</p>', unsafe_allow_html=True)

    # Main Content Area: Futuristic Model + Login Glass Card
    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        try:
            # Use absolute paths for images
            base_path = os.path.dirname(os.path.abspath(__file__))
            mentor_data = get_base64_image(os.path.join(base_path, "assets", "ai_mentor.png"))
            dev_data = get_base64_image(os.path.join(base_path, "assets", "dev_photo.png"))
            logo_data = get_base64_image(os.path.join(base_path, "assets", "kl_logo.png"))

            st.markdown(f"""
<div style='text-align: center; margin-top: 10px;'>
<!-- Institution Header -->
<div class='institution-header'>
{"<img src='data:image/png;base64," + logo_data + "' style='height: 60px;'>" if logo_data else ""}
<div style='text-align: left;'>
<h4 style='margin: 0; color: #00f2fe; font-family: "Orbitron";'>KL UNIVERSITY</h4>
<p style='margin: 0; color: white; font-size: 0.8em; letter-spacing: 2px;'>OFFICIAL CAREER EXCELLENCE HUB</p>
</div>
</div>

<!-- Primary Developer Visual -->
<div style='position: relative; display: flex; justify-content: center; align-items: center;'>
<img src='data:image/png;base64,{dev_data}' class='login-model-img pulse-glow' style='width: 85%; max-width: 450px; border-radius: 30px; border: 4px solid #00f2fe; box-shadow: 0 0 50px rgba(0, 242, 254, 0.4); object-fit: cover;'>
<div style='position: absolute; bottom: -15px; background: linear-gradient(45deg, #00f2fe, #4facfe); color: black; padding: 5px 25px; border-radius: 20px; font-weight: 900; font-family: "Orbitron"; letter-spacing: 2px; box-shadow: 0 5px 20px rgba(0, 242, 254, 0.6);'>DEVELOPER</div>
</div>

<!-- Developer Profile Info -->
<div style='margin-top: 25px; background: rgba(0, 242, 254, 0.08); padding: 25px; border-radius: 20px; border: 1px solid rgba(0, 242, 254, 0.3); backdrop-filter: blur(10px);'>
<h3 style='color: #00f2fe; font-family: "Orbitron"; margin: 0; letter-spacing: 2px;'>BADAM SUDHEER REDDY</h3>
<p style='color: white; font-weight: bold; margin: 8px 0; font-size: 1.1em;'>ID: 2300033278</p>
<p style='color: rgba(255,255,255,0.8); font-size: 1em;'>Computer Science & Engineering @ KL University</p>
<hr style='border: 0.5px solid rgba(0,242,254,0.3); margin: 15px 0;'>
<div style='display: flex; justify-content: center; gap: 15px;'>
<span style='background: linear-gradient(45deg, #7f00ff, #e100ff); color: white; padding: 8px 20px; border-radius: 30px; font-size: 0.85em; font-weight: bold; box-shadow: 0 5px 15px rgba(127, 0, 255, 0.3);'>AI SPECIALIST</span>
<span style='background: linear-gradient(45deg, #00f2fe, #4facfe); color: black; padding: 8px 20px; border-radius: 30px; font-size: 0.85em; font-weight: bold; box-shadow: 0 5px 15px rgba(0, 242, 254, 0.3);'>FULL STACK</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading profile assets: {e}")

    with col2:
        import streamlit.components.v1 as components
        
        st.markdown(f"""
<div class="glass-card">
<div style='text-align: center; margin-bottom: 25px;'>
<span style='font-size: 2.5em; color: #00f2fe; text-shadow: 0 0 15px rgba(0,242,254,0.5);'>🛡️</span>
<h3 style='color: white; font-family: "Orbitron"; margin: 0; letter-spacing: 3px; font-size: 0.9em;'>ENCRYPTED ACCESS GATEWAY</h3>
<p style='color: rgba(255,255,255,0.6); font-size: 0.7em; letter-spacing: 1px; margin-top: 5px;'>SECURE MULTI-NODE AUTHENTICATION</p>
<div style='margin-top: 15px;'>
    <p id='live-clock' style='color: #00f2fe; font-family: "Courier New"; font-weight: bold; font-size: 0.85em; margin: 0; background: rgba(0,0,0,0.6); padding: 8px 15px; border-radius: 8px; display: inline-block; border: 1px solid rgba(0,242,254,0.4); box-shadow: 0 0 10px rgba(0,242,254,0.2);'>⏱️ SYS TIME: INITIATING CLOCK...</p>
</div>
</div>
""", unsafe_allow_html=True)

        components.html("""
        <script>
        function updateTime() {
            const parentDoc = window.parent.document;
            const clock = parentDoc.getElementById('live-clock');
            if (clock) {
                const d = new Date();
                const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
                const nd = new Date(utc + (3600000*5.5));
                const days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
                const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
                let h = nd.getHours();
                let m = nd.getMinutes();
                let s = nd.getSeconds();
                const ampm = h >= 12 ? 'PM' : 'AM';
                h = h % 12;
                h = h ? h : 12;
                m = m < 10 ? '0'+m : m;
                s = s < 10 ? '0'+s : s;
                clock.innerHTML = "⏱️ SYS TIME: " + days[nd.getDay()] + ", " + (nd.getDate()<10?'0':'') + nd.getDate() + " " + months[nd.getMonth()] + " " + nd.getFullYear() + " | " + h + ':' + m + ':' + s + ' ' + ampm + " IST";
            }
        }
        setInterval(updateTime, 1000);
        updateTime();
        </script>
        """, height=0, width=0)
        
        if st.session_state.auth_view == "landing":
            st.markdown("""
            <div style='text-align: center; margin-top: 10px;'>
                <p style='color: #00f2fe; font-family: "Orbitron"; letter-spacing: 2px; font-size: 0.8em;'>CHOOSE YOUR ENTRY PROTOCOL</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_l, col_r = st.columns(2, gap="medium")
            
            with col_l:
                st.markdown("""
                <div class="auth-action-card">
                    <span class="auth-icon">⚡</span>
                    <h4 class="rainbow-text">LOGIN</h4>
                    <p>Access your existing career node</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("ENTER GATEWAY", use_container_width=True, key="go_to_login_btn"):
                    st.session_state.auth_view = "login"
                    st.rerun()
                    
            with col_r:
                st.markdown("""
                <div class="auth-action-card">
                    <span class="auth-icon">🛡️</span>
                    <h4 style="color: #7f00ff; text-shadow: 0 0 10px rgba(127,0,255,0.4);">SIGN UP</h4>
                    <p>Initialize a new identity node</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("JOIN NETWORK", use_container_width=True, key="go_to_signup_btn"):
                    st.session_state.auth_view = "signup"
                    st.rerun()
            
            st.markdown("""
            <div style='text-align: center; margin-top: 50px;'>
                <p style='color: rgba(255,255,255,0.3); font-size: 0.65em; letter-spacing: 1px;'>SECURED BY QUANTUM ENCRYPTION v4.0.2</p>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state.auth_view == "login":
            st.markdown("""
<p class='rainbow-text' style='font-size: 0.9em; text-align: center; margin-bottom: 20px; font-weight: 900; letter-spacing: 1px;'>
⚠️ ALL FIELDS INCLUDING CAPTCHA ARE MANDATORY
</p>
""", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #00f2fe; font-family: Orbitron; margin-bottom: 20px; text-align: center;'>SYSTEM ACCESS</h3>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                uni_in = st.selectbox("UNIVERSITY / COLLEGE", COLLEGE_NAMES, key="login_uni", help="Start typing to search your institution")
                roll_in = st.text_input("STUDENT ID (ROLL NO)", key="login_roll")
                u_in = st.text_input("QUANTUM IDENTITY (USERNAME/EMAIL)", key="login_user")
                p_in = st.text_input("SECURITY KEY (PASSWORD)", type="password", key="login_pass")
                
                st.markdown("<div class='captcha-box'>", unsafe_allow_html=True)
                st.markdown(f"""
<div style='text-align: center;'>
<p style='margin: 0; color: #00f2fe; font-size: 0.7em; letter-spacing: 2px;'>VERIFICATION CODE</p>
<h1 style='letter-spacing: 15px; color: white; margin: 10px 0; font-family: "Courier New"; text-shadow: 0 0 10px #00f2fe;'>{st.session_state.captcha}</h1>
</div>
""", unsafe_allow_html=True)
                
                captcha_in = st.text_input("TYPE CODE", key="captcha_in")
                st.markdown("</div>", unsafe_allow_html=True)
                
                not_robot = st.checkbox("I AM HUMAN (TURING TEST)", key="robot_check")
                
                st.markdown("<div class='glowing-btn'>", unsafe_allow_html=True)
                submit_login = st.form_submit_button("AUTHENTICATE SYSTEM", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                if submit_login:
                    with st.spinner("🔐 ESTABLISHING SECURE NEURAL LINK..."):
                        u, p, c = u_in.strip(), p_in.strip(), captcha_in.strip()
                        uni, roll = uni_in.strip(), roll_in.strip()
                        if not u or not p or not c or not uni or not roll:
                            st.warning("All fields including University Name, Student ID, and CAPTCHA are required.")
                        elif not not_robot:
                            st.error("Human verification failed. Please check the 'I AM HUMAN' box.")
                        elif c != st.session_state.captcha:
                            st.error("Verification code mismatch. (Note: Case Sensitive)")
                            st.session_state.captcha = generate_captcha()
                            st.rerun()
                        else:
                            user = login_user(u, p)
                            if isinstance(user, dict) and user.get("status") == "blocked":
                                st.error(f"🛑 ACCESS RESTRICTED: {user['message']}")
                            elif user:
                                st.toast("✅ IDENTITY VERIFIED", icon="🛡️")
                                st.session_state.logged_in = True
                                st.session_state.user = {"id": user[0], "username": user[1], "role": user[2], "university": user[4]}
                                final_uni = uni if uni else (user[4] if user[4] else "KL UNIVERSITY")
                                st.session_state.watermark_info = f"{final_uni} - {roll}"
                                st.rerun()
                            else:
                                st.error("ACCESS DENIED: INVALID QUANTUM IDENTITY.")
            
            col_back, col_reg = st.columns(2)
            with col_back:
                if st.button("← BACK", use_container_width=True, key="back_to_land_login"):
                    st.session_state.auth_view = "landing"
                    st.rerun()
            with col_reg:
                if st.button("NEW IDENTITY?", use_container_width=True, key="to_reg_from_login"):
                    st.session_state.auth_view = "signup"
                    st.rerun()

            st.markdown("---")
            with st.expander("🔑 LOST ACCESS? INITIATE RECOVERY"):
                st.markdown("""
                <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 3px solid #ff7675;'>
                    <p style='font-size: 0.8em; color: #ff7675; margin: 0;'><b>NEURAL RECOVERY PROTOCOL</b></p>
                    <p style='font-size: 0.7em; color: rgba(255,255,255,0.6); margin: 0;'>Provide your identifier to initiate security challenge.</p>
                </div>
                """, unsafe_allow_html=True)
                
                f_user = st.text_input("QUANTUM IDENTIFIER (USERNAME/EMAIL)", key="forgot_user")
                if f_user:
                    q = get_security_question(f_user)
                    if q:
                        st.markdown(f"""
                        <div style='margin: 15px 0; padding: 10px; background: rgba(0, 242, 254, 0.1); border-radius: 8px; border: 1px dashed #00f2fe;'>
                            <p style='font-size: 0.75em; color: #00f2fe; margin-bottom: 5px;'>SECURITY CHALLENGE:</p>
                            <p style='font-weight: bold; color: white;'>{q}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        f_answer = st.text_input("KEY ANSWER", key="forgot_answer", placeholder="Enter your secret answer...")
                        new_p = st.text_input("NEW SECURITY KEY", type="password", key="forgot_new_p", placeholder="Set a strong new password...")
                        
                        st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
                        if st.button("RESET SYSTEM ACCESS", use_container_width=True):
                            if not f_answer or not new_p:
                                st.warning("Please provide both the answer and the new password.")
                            elif f_user.upper() == "BADAM SUDHEER REDDY":
                                st.error("CRITICAL ERROR: Developer account recovery must be performed via Master Terminal only.")
                            elif reset_password(f_user, f_answer, new_p):
                                st.success("PROTOCOL SUCCESS: SECURITY KEY UPDATED.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("CHALLENGE FAILED: INCORRECT KEY ANSWER.")
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("IDENTIFIER NOT RECOGNIZED BY THE NETWORK.")

        elif st.session_state.auth_view == "signup":
            st.markdown("<h3 style='color: #7f00ff; font-family: Orbitron; margin-bottom: 20px; text-align: center;'>CREATE IDENTITY</h3>", unsafe_allow_html=True)
            with st.form("reg_form"):
                new_uni_in = st.selectbox("YOUR UNIVERSITY / COLLEGE", COLLEGE_NAMES, key="reg_uni")
                new_u_in = st.text_input("QUANTUM NAME", key="reg_user")
                new_e_in = st.text_input("IDENTITY EMAIL", key="reg_email")
                new_p_in = st.text_input("ACCESS KEY", key="reg_pass", type="password")
                new_c_in = st.text_input("CONFIRM KEY", key="reg_confirm", type="password")
                
                st.markdown("---")
                st.write("🛡️ **SECURITY RECOVERY PROTOCOL**")
                s_quest = st.selectbox("RECOVERY QUESTION", [
                    "What was your first school?",
                    "What is your mother's maiden name?",
                    "What is your pet's name?",
                    "Which city were you born in?",
                    "What was your favorite childhood toy?"
                ])
                s_ans_in = st.text_input("PROTOCOL ANSWER", key="reg_s_ans")
                
                st.markdown("---")
                terms_agreed = st.checkbox("I agree to the Terms & Conditions and Privacy Policy.", key="reg_terms")
                
                st.markdown("<div class='glowing-btn'>", unsafe_allow_html=True)
                submit_reg = st.form_submit_button("INITIALIZE IDENTITY", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                if submit_reg:
                    with st.spinner("🛡️ INITIALIZING IDENTITY PROTOCOLS..."):
                        nu, ne, np, nc = new_u_in.strip(), new_e_in.strip(), new_p_in.strip(), new_c_in.strip()
                        sa = s_ans_in.strip()
                        if not terms_agreed:
                            st.warning("You must agree to the Terms & Conditions to proceed.")
                        elif not nu or not ne or not np or not sa:
                            st.warning("All fields are mandatory.")
                        elif np != nc:
                            st.error("KEYS DO NOT MATCH")
                        elif nu.upper() == "BADAM SUDHEER REDDY":
                            st.error("ACCESS DENIED: THIS IDENTITY IS RESERVED FOR THE PRIMARY DEVELOPER.")
                        elif register_user(nu, ne, np, new_uni_in, s_quest, sa, "0000000000"):
                            st.toast("🌐 IDENTITY SYNC COMPLETE", icon="✅")
                            st.success("IDENTITY INITIALIZED. ACCESS GRANTED.")
                            time.sleep(1)
                            st.session_state.auth_view = "login"
                            st.rerun()
                        else:
                            st.error("IDENTITY ALREADY EXISTS.")
            
            col_back, col_log = st.columns(2)
            with col_back:
                if st.button("← BACK", use_container_width=True, key="back_to_land_reg"):
                    st.session_state.auth_view = "landing"
                    st.rerun()
            with col_log:
                if st.button("HAVE ACCOUNT?", use_container_width=True, key="to_login_from_reg"):
                    st.session_state.auth_view = "login"
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Global Stats Footer
    st.markdown("<div style='margin-top: 50px;'>", unsafe_allow_html=True)
    try:
        total_users, _ = get_community_stats()
        st.markdown(f"""
<div style='text-align: center; background: rgba(0, 242, 254, 0.05); padding: 20px; border-radius: 20px; border: 1px solid rgba(0, 242, 254, 0.2);'>
<p style='color: white; margin: 0; font-family: "Orbitron"; letter-spacing: 2px;'>
<span style='color: #00f2fe;'>{total_users}</span> ACTIVE NODES IN THE NETWORK
</p>
</div>
""", unsafe_allow_html=True)
    except:
        pass
    st.markdown("</div>", unsafe_allow_html=True)

def sidebar_nav():
    st.sidebar.markdown(f"<h1 class='tricolor-text' style='font-size: 1.8em; font-family: \"Orbitron\", sans-serif;'>👋 Hello, {st.session_state.user['username']}</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    nav_options = ["🏠 Dashboard", "💬 AI Career Assistant", "🎯 AI Placement Predictor", "📄 Resume Analyzer", "📝 Aptitude Quiz", "📚 Career Resources", "💻 Coding Tracker", "📊 Skill Tracker", "📞 Support & Feedback", "⚙️ Settings"]
    
    # Add Developer Panel exclusively for the Developer
    current_user = st.session_state.user.get('username', '').upper()
    if current_user == 'BADAM SUDHEER REDDY':
        nav_options.append("👨‍💻 Developer Control Center")
        
    page = st.sidebar.radio("Navigate", nav_options)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.dev_verified = False
        st.session_state.auth_view = "landing"
        st.rerun()

    # Developer Credits
    st.sidebar.markdown("---")
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        dev_path = os.path.join(base_path, "assets", "dev_photo.png")
        if os.path.exists(dev_path):
            with open(dev_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            st.sidebar.markdown(
                f"""
<div style="text-align: center;">
<img src="data:image/png;base64,{data}" class="tricolor-glow" style="border-radius: 50%; width: 150px; height: 150px; object-fit: cover; margin-bottom: 15px;">
</div>
""",
                unsafe_allow_html=True
            )
        else:
            st.sidebar.markdown("👤")
    except Exception as e:
        st.sidebar.markdown("👤") 

    st.sidebar.markdown("""
<div style='text-align: center;'>
<p class='tricolor-text' style='font-weight: bold; margin-bottom: 0; font-size: 1.1em;'>🚀 Developed by:</p>
<p class='tricolor-text' style='font-size: 1.3em; font-weight: 900; margin-bottom: 0; letter-spacing: 1px;'>BADAM SUDHEER REDDY</p>
<p class='tricolor-text' style='font-size: 1em; font-weight: bold;'>ID: 2300033278</p>
<p class='tricolor-text' style='font-size: 0.9em; font-weight: bold;'>KL UNIVERSITY</p>
</div>
""", unsafe_allow_html=True)

    # --- DYNAMIC AI MENTOR TIPS ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 AI MENTOR GUIDANCE")
    
    tips_map = {
        "🏠 Dashboard": "Welcome! Start by checking your 'Placement Readiness' score. It gives you a bird's-eye view of your current standing.",
        "💬 AI Career Assistant": "I am here to help! Ask me anything about interviews, resumes, or coding logic.",
        "🎯 AI Placement Predictor": "Be honest with your metrics. The AI uses these to calculate your probability of success in real campus drives.",
        "📄 Resume Analyzer": "Upload a PDF resume. The AI will check for ATS-friendly keywords and point out missing technical skills.",
        "📝 Aptitude Quiz": "Speed is as important as accuracy. Aim to finish the quiz within the time limit to simulate real rounds.",
        "📚 Career Resources": "Focus on the 'Top Interview Questions' section. 80% of companies ask these fundamentals.",
        "💻 Coding Tracker": "Consistency is key. Try to log at least one problem daily to maintain your technical momentum.",
        "📊 Skill Tracker": "Add skills that are currently in high demand like React, Node.js, or AWS to increase your marketability.",
        "📞 Support & Feedback": "Need help? Send us a message! We're constantly improving the system based on your needs.",
        "⚙️ Settings": "Keep your profile updated. Your phone number and email are used for official campus placement alerts.",
        "👨‍💻 Developer Control Center": "Hello Developer! Use this panel to monitor system health and ensure all nodes are functioning correctly."
    }
    
    current_tip = tips_map.get(page, "Keep pushing forward! Every small step brings you closer to your dream placement.")
    st.sidebar.info(f"💡 **Pro-Tip:** {current_tip}")

    # Routing
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎯 AI Placement Predictor":
        show_predictor()
    elif page == "📄 Resume Analyzer":
        show_resume_analyzer()
    elif page == "📝 Aptitude Quiz":
        show_quiz()
    elif page == "📚 Career Resources":
        show_resources()
    elif page == "💻 Coding Tracker":
        show_coding_tracker()
    elif page == "📊 Skill Tracker":
        show_skill_tracker()
    elif page == "📞 Support & Feedback":
        show_support()
    elif page == "⚙️ Settings":
        show_settings()
    elif page == "👨‍💻 Developer Control Center":
        show_developer_dashboard()
    elif page == "💬 AI Career Assistant":
        show_ai_assistant()

def show_ai_assistant():
    st.markdown("<h1 class='neon-title'>💬 AI Career Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>YOUR 24/7 PERSONAL PLACEMENT MENTOR</p>", unsafe_allow_html=True)
    
    st.info("💡 I am powered by advanced Generative AI. Ask me about coding problems, interview strategies, or resume tips!")
    
    # API Key Management for Real AI
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
        
    col_api, col_help = st.columns([3, 1])
    with col_api:
        api_key = st.text_input(
            "🔐 Enter Google Gemini API Key:", 
            value=st.session_state.gemini_api_key, 
            type="password",
            help="This key activates the advanced AI engine. Without it, the assistant runs in a basic offline demo mode."
        )
    with col_help:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("❓ HELP", use_container_width=True):
            st.session_state.show_api_help = not st.session_state.get('show_api_help', False)

    if st.session_state.get('show_api_help', False):
        st.info("""
        ### 🔑 How to get your FREE Gemini API Key:
        1. Visit **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
        2. Sign in with your Google Account.
        3. Click **"Create API key"**.
        4. Copy the key and paste it here!
        
        *Note: The Free Tier allows plenty of requests for personal preparation.*
        """)

    if api_key:
        st.session_state.gemini_api_key = api_key
        st.success("✅ Neural link established. The True AI Engine is now fully operational!")
    else:
        st.warning("⚠️ The AI is running in offline demo mode. Please provide a Gemini API Key for real-time intelligent responses.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI Mentor. How can I assist you with your placement preparation today?"}
        ]

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask your AI Mentor a question..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Identity Overrides
        prompt_lower = prompt.lower()
        if "who are you" in prompt_lower:
            response = "I am PlaceMentor AI, an advanced virtual career assistant designed specifically for KL University students. I'm here 24/7 to help you crack your dream placement by providing resume feedback, coding strategies, and interview tips!"
        elif "who developed you" in prompt_lower or "who devolped you" in prompt_lower or "who developed this" in prompt_lower or "who devolped this" in prompt_lower or "who created you" in prompt_lower:
            response = "I was conceptualized and developed by **Badam Sudheer Reddy**, an AI Specialist and Full-Stack Developer at KL University. He built me to serve as the ultimate career intelligence system for students."
        else:
            if st.session_state.gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    # Using gemini-1.5-flash or gemini-pro
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    context = "You are PlaceMentor AI, a highly intelligent and supportive AI Career Mentor for college students. Provide concise, helpful advice for placements, coding, and resumes. "
                    ai_response = model.generate_content(context + "Student asks: " + prompt)
                    response = ai_response.text
                except ImportError:
                    response = "⚠️ **Error:** The `google-generativeai` library is missing. Developer: Please run `pip install google-generativeai` in your terminal to enable the true AI engine."
                except Exception as e:
                    response = f"⚠️ **API Error:** {str(e)}. Please check if your API key is valid and you have an active internet connection."
            else:
                response = f"*[OFFLINE MODE]*: That's a great question about '{prompt}'. To get a highly detailed and intelligent answer, please enter your Gemini API Key at the top of this page to activate the true AI Search Engine!"
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def show_developer_dashboard():
    # Master Security Check for Developer
    if 'dev_verified' not in st.session_state:
        st.session_state.dev_verified = False
        
    if not st.session_state.dev_verified:
        st.markdown("<h1 class='neon-title' style='font-size: 2.5rem !important;'>🔐 IDENTITY VERIFICATION</h1>", unsafe_allow_html=True)
        st.info("⚠️ This is a restricted area. Please enter your Master Security PIN to continue.")
        col_pin, col_btn = st.columns([2, 1])
        with col_pin:
            pin = st.text_input("MASTER PROTOCOL PIN", type="password", placeholder="Enter PIN...")
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("AUTHENTICATE", use_container_width=True):
                if pin == "2300033278": # Developer's ID as Master PIN
                    st.session_state.dev_verified = True
                    st.success("VERIFICATION SUCCESSFUL!")
                    st.rerun()
                else:
                    st.error("INVALID PROTOCOL PIN.")
        return

    st.markdown("<h1 class='neon-title' style='font-size: 3rem !important;'>DEVELOPER CONTROL CENTER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>SYSTEM AUDIT & USER MONITORING</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 User Analytics", "🛡️ Security Logs", "💬 User Feedback", "📢 Manage Notices"])
    
    with tab1:
        st.subheader("Active Nodes Performance")
        stats = get_all_user_stats()
        if stats:
            import pandas as pd
            df = pd.DataFrame(stats, columns=["Username", "Email", "College", "Student ID", "Last Login", "Coding Problems", "Avg Quiz Score", "Skills Count"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No user data available.")
            
        st.markdown("---")
        st.subheader("🗑️ Remove User Node")
        with st.form("remove_user_form"):
            user_to_remove = st.text_input("Username to Remove", placeholder="Enter exact username...")
            confirm_check = st.checkbox("I confirm that I want to permanently delete this user and all their data.")
            submit_remove = st.form_submit_button("REMOVE USER PERMANENTLY")
            
            if submit_remove:
                if not user_to_remove:
                    st.warning("Please enter a username.")
                elif not confirm_check:
                    st.error("Please confirm the deletion.")
                elif user_to_remove.upper() == "BADAM SUDHEER REDDY":
                    st.error("Access Denied: You cannot remove the primary developer account.")
                else:
                    success, message = delete_user(user_to_remove)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown("---")
        st.subheader("🛡️ Block / Restrict User Access")
        
        # Show live user status table
        try:
            import pandas as pd
            conn_tmp = __import__('sqlite3').connect("database/placementor.db")
            cur_tmp = conn_tmp.cursor()
            cur_tmp.execute("SELECT username, email, status, block_message FROM users ORDER BY username")
            user_rows = cur_tmp.fetchall()
            conn_tmp.close()
            if user_rows:
                df_status = pd.DataFrame(user_rows, columns=["Username", "Email", "Status", "Block Message"])
                df_status["Status"] = df_status["Status"].fillna("active")
                st.dataframe(df_status, use_container_width=True)
        except Exception as e:
            st.caption(f"Could not load user list: {e}")

        with st.form("block_user_form"):
            st.caption("💡 Username matching is **case-insensitive**. Refer to the table above for exact usernames.")
            user_to_block = st.text_input("Username to Target", placeholder="Enter username (e.g. john_doe)...")
            action = st.radio("Action", ["Block Access", "Restore Access"], horizontal=True)
            block_msg = st.text_area(
                "Admin Message (shown to user on login)",
                placeholder="e.g. Your account has been suspended due to policy violations. Contact admin@kluniversity.in to appeal."
            )
            submit_block = st.form_submit_button("🔒 UPDATE ACCOUNT STATUS", use_container_width=True)
            
            if submit_block:
                if not user_to_block:
                    st.warning("⚠️ Please enter a username.")
                elif user_to_block.upper() == "BADAM SUDHEER REDDY":
                    st.error("🚫 Access Denied: You cannot block the primary developer account.")
                else:
                    new_status = 'blocked' if action == "Block Access" else 'active'
                    success, message = update_user_status(user_to_block, new_status, block_msg)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
    with tab2:
        st.subheader("Quantum Security Audit")
        logs = get_security_logs()
        if logs:
            import pandas as pd
            df_logs = pd.DataFrame(logs, columns=["Username", "Event", "Timestamp"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("No security logs detected.")
            
    with tab3:
        st.subheader("Support Tickets")
        feedback = get_all_feedback()
        if feedback:
            for f in feedback:
                with st.expander(f"Subject: {f[1]} | From: {f[0]}"):
                    st.write(f"**Message:** {f[2]}")
                    st.write(f"*Received: {f[3]}*")
        else:
            st.info("No feedback received yet.")
            
    with tab4:
        st.subheader("Manage Campus Notices")
        
        # Add new notice
        with st.form("add_notice_form"):
            new_notice = st.text_input("New Notice Content", placeholder="Enter notice here...")
            submitted = st.form_submit_button("Post Notice")
            if submitted and new_notice:
                post_notice(new_notice)
                st.success("Notice posted successfully!")
                st.rerun()
                
        # Sync Live Updates
        st.markdown("---")
        st.subheader("🌐 Social & Official Sync")
        st.write("Fetch latest updates directly from KL University's official channels (Website, Social Media).")
        if st.button("⚡ SYNC KLU LIVE UPDATES", use_container_width=True):
            with st.spinner("Connecting to KLU Neural Feed..."):
                live_data = fetch_klu_live_notices()
                if live_data:
                    for item in live_data:
                        # Prevent duplicate syncs by checking if already posted (basic check)
                        post_notice(item['content'])
                    st.success(f"Successfully synced {len(live_data)} live updates!")
                    st.rerun()
                else:
                    st.error("Could not reach official servers. Try again later.")

        # List and delete existing notices
        st.markdown("---")
        st.markdown("**Active Notices:**")
        notices = get_notices()
        if notices:
            for nid, n, d in notices:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.info(f"🔔 {n} (Posted: {d})")
                with col2:
                    if st.button("Delete", key=f"del_notice_{nid}"):
                        delete_notice(nid)
                        st.success("Notice deleted!")
                        st.rerun()
        else:
            st.info("No active notices.")

def show_dashboard():
    st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
    
    # KL University Branding Header (logo pre-cached)
    st.markdown(f"""
        <div style='background-color: #ffffff; padding: 15px; border-radius: 15px; border-left: 5px solid #6c5ce7; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;'>
            <div style='display: flex; align-items: center; gap: 20px;'>
                <img src='data:image/png;base64,{get_base64_image("assets/kl_logo.png")}' style='height: 60px;'>
                <div>
                    <h4 style='margin: 0; color: #2d3436;'>KL UNIVERSITY 🏛️</h4>
                    <p style='margin: 0; color: #636e72; font-size: 0.9em;'>Official Career Excellence Portal</p>
                </div>
            </div>
            <div>
                <p id='dash-live-clock' style='color: #6c5ce7; font-family: "Courier New"; font-weight: bold; font-size: 0.85em; margin: 0; background: rgba(108, 92, 231, 0.1); padding: 8px 15px; border-radius: 8px; border: 1px solid rgba(108, 92, 231, 0.3);'>⏱️ IST: Loading...</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    import streamlit.components.v1 as components
    components.html("""
    <script>
    function updateDashTime() {
        const clock = window.parent.document.getElementById('dash-live-clock');
        if (clock) {
            const nd = new Date(new Date().toLocaleString("en-US", {timeZone: "Asia/Kolkata"}));
            const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
            const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
            let h = nd.getHours(), m = nd.getMinutes(), s = nd.getSeconds();
            const ampm = h >= 12 ? 'PM' : 'AM';
            h = h % 12 || 12;
            clock.textContent = `⏱️ IST: ${days[nd.getDay()]}, ${String(nd.getDate()).padStart(2,'0')} ${months[nd.getMonth()]} ${nd.getFullYear()} | ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')} ${ampm}`;
        }
    }
    setInterval(updateDashTime, 1000);
    updateDashTime();
    </script>
    """, height=0, width=0)
    
    # Fetch real data
    total_problems, platforms = get_coding_stats(st.session_state.user['id'])
    scores = get_user_scores(st.session_state.user['id'])
    avg_score = sum([s[1] for s in scores]) / len(scores) if scores else 0
    skills = get_user_skills(st.session_state.user['id'])
    readiness = min(100, (len(skills) * 8) + (total_problems // 2) + (avg_score // 4))

    st.title("🚀 Your Career Dashboard")
    
    st.info(f"👋 Welcome back, **{st.session_state.user['username']}**! Your career progression is currently being monitored by PlaceMentor AI. We are here to support your success at every step.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Placement Readiness", f"{readiness}%")
    with col2:
        st.metric("Avg Quiz Score", f"{avg_score:.1f}/100")
    with col3:
        st.metric("Code Problems", str(total_problems))
    with col4:
        st.metric("Skills Tracked", str(len(skills)))

    # AI Career Radar (BEST FEATURE)
    st.markdown("""
        <div style='background: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #00cec9; margin-bottom: 25px;'>
            <h4 style='margin: 0; color: #2d3436;'>🧠 AI Career Radar Analysis</h4>
            <p style='margin: 0; color: #636e72; font-size: 0.9em;'>Multi-dimensional breakdown of your placement readiness.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Generate Radar Data
    categories = ['Aptitude', 'Technical', 'Coding', 'Communication', 'Resume', 'Confidence']
    # Simulated metrics based on user data
    values = [
        avg_score, 
        min(100, len(skills) * 15), 
        min(100, total_problems * 2), 
        85 if len(skills) > 3 else 60,
        75 if total_problems > 10 else 50,
        readiness
    ]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        line_color='#00cec9',
        fillcolor='rgba(0, 206, 201, 0.3)'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=380,
        margin=dict(l=50, r=50, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})

    # Career Insights Bar Chart (replaces heavy 3D plot for instant rendering)
    st.markdown("""
        <div style='background: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #6c5ce7; margin-bottom: 25px; margin-top: 25px;'>
            <h4 style='margin: 0; color: #2d3436;'>📊 Career Dimension Analysis</h4>
            <p style='margin: 0; color: #636e72; font-size: 0.9em;'>Your performance across key placement dimensions.</p>
        </div>
    """, unsafe_allow_html=True)
    fig_bar = go.Figure(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=values,
            colorscale='Turbo',
            showscale=False
        )
    ))
    fig_bar.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 100], gridcolor='rgba(0,0,0,0.05)')
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")
    
    # Dashboard Layout Columns
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("🎯 Placement Readiness Check")
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = readiness,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#6c5ce7"},
                'steps': [
                    {'range': [0, 40], 'color': "#ff7675"},
                    {'range': [40, 75], 'color': "#ffeaa7"},
                    {'range': [75, 100], 'color': "#55efc4"}
                ]
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #6c5ce7, #a29bfe); padding: 15px; border-radius: 15px; color: white; margin-bottom: 20px;'>
                <h4 style='margin: 0; color: white;'>📢 Campus Notices</h4>
            </div>
        """, unsafe_allow_html=True)
        notices = get_notices()
        if notices:
            for nid, n, d in notices:
                is_live = "[Live]" in n or "[Social]" in n
                if is_live:
                    st.markdown(f"""
                        <div style='background: rgba(108, 92, 231, 0.05); padding: 12px; border-radius: 10px; border: 1px solid rgba(108, 92, 231, 0.2); margin-bottom: 10px; position: relative; overflow: hidden;'>
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                                <span style='background: #ff4757; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.6em; font-weight: bold; animation: pulse 2s infinite;'>LIVE UPDATE</span>
                                <span style='font-size: 0.7em; color: #636e72;'>{d}</span>
                            </div>
                            <p style='margin: 0; color: #2d3436; font-size: 0.85em; font-weight: 500;'>{n.replace("[Live] ", "").replace("[Social] ", "")}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style='background: #f1f2f6; padding: 12px; border-radius: 10px; margin-bottom: 10px;'>
                            <p style='margin: 0; color: #2d3436; font-size: 0.85em;'>{n}</p>
                            <p style='margin-top: 5px; margin-bottom: 0; font-size: 0.7em; color: #636e72;'>📅 {d}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active notices.")
        
        st.markdown("---")
        st.subheader("✅ Prep Checklist")
        st.checkbox("Update Resume with latest projects", value=True)
        st.checkbox("Analyze Resume with JD Matcher", value=False)
        st.checkbox("Practice Mock Aptitude Quiz", value=True)
        st.checkbox("Log 5 Coding Problems this week", value=False)
        st.checkbox("Complete Technical Profile", value=len(skills) > 3)
        
        st.markdown("---")
        st.subheader("💡 Placement Tip")
        tips = [
            "Research the company before the interview. Knowing their products makes a great impression!",
            "Be prepared to explain every single project listed on your resume in detail.",
            "Always have 2-3 thoughtful questions ready to ask the interviewer at the end.",
            "Practice basic HR questions like 'Tell me about yourself' until you sound confident.",
            "Focus on Data Structures and Algorithms; they are the foundation of technical rounds."
        ]
        st.info(f"💡 Tip: {random.choice(tips)}")
        
        # --- CERTIFICATE SECTION ---
        st.markdown("---")
        if readiness >= 80:
            st.success("🏆 **Level Elite Reached!** You are now eligible for your Placement Readiness Certificate.")
            
            # Extract info for certificate
            user_name = st.session_state.user['username']
            # Try to get uni/roll from watermark info if available
            watermark = st.session_state.get('watermark_info', "KL University - Student")
            uni = watermark.split(" - ")[0] if " - " in watermark else "KL University"
            
            from datetime import datetime
            today = datetime.now().strftime("%d %b, %Y")
            
            try:
                pdf_bytes = generate_certificate(user_name, uni, readiness, today)
                st.download_button(
                    label="📜 DOWNLOAD MY CERTIFICATE",
                    data=pdf_bytes,
                    file_name=f"Placement_Readiness_{user_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating certificate: {e}")
        else:
            st.warning(f"🔒 **Certificate Locked**: Reach **80% Readiness** to unlock your official certification. (Current: {readiness}%)")
    
    # Supportive System Health Footer
    st.markdown("---")
    scol1, scol2 = st.columns([2, 1])
    with scol1:
        st.markdown("""
            <div style='background: rgba(0, 206, 201, 0.05); padding: 20px; border-radius: 20px; border: 1px solid rgba(0, 206, 201, 0.3);'>
                <h5 style='color: #00b894; margin-top: 0; font-family: "Orbitron"; letter-spacing: 1px;'>🛡️ SYSTEM INTEGRITY & SUPPORT</h5>
                <p style='font-size: 0.9em; color: #2d3436; margin-bottom: 10px;'>
                    PlaceMentor AI is actively monitoring your preparation flow. If you experience any technical issues or need career guidance, our support infrastructure is ready.
                </p>
                <p style='font-size: 1em; color: #6c5ce7; font-weight: bold;'>
                    ✨ YOU ARE NOT ALONE IN THIS JOURNEY!
                </p>
                <div style='display: flex; gap: 10px; margin-top: 15px;'>
                    <div style='background: #55efc4; width: 10px; height: 10px; border-radius: 50%;'></div>
                    <span style='font-size: 0.7em; color: #636e72;'>CORE ENGINE: ONLINE</span>
                    <div style='background: #00f2fe; width: 10px; height: 10px; border-radius: 50%; margin-left: 10px;'></div>
                    <span style='font-size: 0.7em; color: #636e72;'>SUPPORT NODES: READY</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with scol2:
        if st.button("🆘 REQUEST INSTANT ASSISTANCE", use_container_width=True):
            st.toast("Support request received! Opening ticket...")
            time.sleep(1)
            # Log the emergency ticket to the database
            send_feedback(st.session_state.user['id'], "🚨 EMERGENCY ASSISTANCE REQUIRED", "User triggered the Instant Assistance protocol from their main dashboard.")
            st.success("TICKET OPENED. A mentor will contact you shortly.")
        
        # KL University Official Hub
        st.markdown("""
            <div style='background: #ffffff; padding: 20px; border-radius: 15px; border-top: 5px solid #e84393; margin-top: 30px;'>
                <h4 style='margin: 0; color: #2d3436;'>🏛️ KL University Official Hub</h4>
                <p style='color: #636e72; font-size: 0.9em; margin-bottom: 15px;'>Stay updated with official campus announcements.</p>
                <div style='display: flex; gap: 15px; flex-wrap: wrap;'>
                    <a href='https://www.facebook.com/KLUniversity/' target='_blank' style='text-decoration: none;'>
                        <div style='background: #1877F2; color: white; padding: 8px 15px; border-radius: 10px; font-size: 0.8em;'>Facebook</div>
                    </a>
                    <a href='https://www.instagram.com/kluniversityofficial/' target='_blank' style='text-decoration: none;'>
                        <div style='background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: white; padding: 8px 15px; border-radius: 10px; font-size: 0.8em;'>Instagram</div>
                    </a>
                    <a href='https://twitter.com/kluniversity' target='_blank' style='text-decoration: none;'>
                        <div style='background: #1DA1F2; color: white; padding: 8px 15px; border-radius: 10px; font-size: 0.8em;'>Twitter (X)</div>
                    </a>
                    <a href='https://www.youtube.com/user/kluniversity' target='_blank' style='text-decoration: none;'>
                        <div style='background: #FF0000; color: white; padding: 8px 15px; border-radius: 10px; font-size: 0.8em;'>YouTube</div>
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.write(f"💻 **Coding:** {total_problems} Problems Logged")
    
    # Community Insights
    st.markdown("---")
    st.subheader("👥 Community Insights")
    total_users, recent_activity = get_community_stats()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"""
            <div style='background: white; padding: 20px; border-radius: 15px; text-align: center; border-bottom: 5px solid #00cec9;'>
                <h2 class='digital-num' style='color: #00cec9; margin: 0;'>{total_users}</h2>
                <p style='color: #636e72; margin: 0;'>Total Registered Students</p>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown("**Recent Activity**")
        for user, date in recent_activity:
            st.caption(f"👤 **{user}** was active at {date}")

    st.markdown('</div>', unsafe_allow_html=True)

# Placeholder functions for pages (will be moved to pages/ if needed or kept modular)
def show_predictor():
    from utils.ml_model import predict_placement
    st.markdown("<h1 class='neon-title' style='font-size: 3.5rem !important;'>🎯 AI PLACEMENT PREDICTOR</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>HIGH-PRECISION NEURAL INFERENCE ENGINE</p>", unsafe_allow_html=True)
    
    st.info("💡 Our Random Forest model analyzes 12+ performance parameters to calculate your success probability with 94% accuracy.")
    
    # High-Precision Digital Input Panel
    st.markdown("""
        <div style='background: rgba(0, 242, 254, 0.05); padding: 30px; border-radius: 25px; border: 1px solid rgba(0, 242, 254, 0.3); margin-bottom: 30px;'>
            <h4 style='color: #00f2fe; font-family: "Orbitron"; letter-spacing: 2px; margin-bottom: 25px;'>⚙️ NEURAL INPUT CONFIGURATION</h4>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<p style='color: #00f2fe; font-weight: bold; margin-bottom: 5px;'>📊 ACADEMIC PRECISION (CGPA)</p>", unsafe_allow_html=True)
        cgpa = st.number_input("CGPA (SCALE: 0.00 - 10.00)", 0.0, 10.0, 8.50, 0.01, key="main_cgpa")
        
        # Quick-Set Digital Presets
        st.markdown("<p style='font-size: 0.7em; color: rgba(255,255,255,0.5);'>DIGITAL PRESETS:</p>", unsafe_allow_html=True)
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1: 
            if st.button("7.50", key="c75", use_container_width=True): 
                st.session_state.main_cgpa = 7.50
                st.rerun()
        with cp2:
            if st.button("8.00", key="c80", use_container_width=True): 
                st.session_state.main_cgpa = 8.00
                st.rerun()
        with cp3:
            if st.button("8.50", key="c85", use_container_width=True): 
                st.session_state.main_cgpa = 8.50
                st.rerun()
        with cp4:
            if st.button("9.00", key="c90", use_container_width=True): 
                st.session_state.main_cgpa = 9.00
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        aptitude = st.slider("🧠 APTITUDE SCORE (VERBAL & QUANT)", 0, 100, 75, help="Based on your internal mock tests.")
        coding = st.slider("💻 CODING PROFICIENCY (DSA & LOGIC)", 0, 100, 70, help="Your average score in competitive coding.")
        
    with col2:
        comms = st.select_slider("🗣️ COMMUNICATION BANDWIDTH", options=list(range(1, 11)), value=7, help="Rate your verbal and non-verbal skills.")
        projects = st.number_input("🛠️ FULL-STACK PROJECTS COMPLETED", 0, 10, 2)
        technical = st.number_input("🛡️ CORE TECHNICAL SKILLS (VETTED)", 0, 20, 5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 15px; border-left: 4px solid #fdcb6e;'>
                <p style='color: #fdcb6e; font-size: 0.85em; margin: 0;'>
                    <b>Note:</b> These values are cross-verified with your 'Skill Tracker' and 'Coding Tracker' for final reporting.
                </p>
            </div>
        """, unsafe_allow_html=True)

    if st.button("Predict Probability"):
        res, prob = predict_placement(cgpa, aptitude, coding, comms, projects, technical)
        
        st.markdown("---")
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            if res == 1:
                st.success("### Prediction: High Likelihood of Placement!")
            else:
                st.warning("### Prediction: Work Harder to Improve!")
            
            st.write(f"Confidence Score: {prob*100:.2f}%")
        
        with col_res2:
            import plotly.graph_objects as go
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = prob * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Placement Probability (%)"},
                gauge = {'axis': {'range': [None, 100]},
                        'bar': {'color': "#6c5ce7"},
                        'steps' : [
                            {'range': [0, 50], 'color': "#ff7675"},
                            {'range': [50, 80], 'color': "#ffeaa7"},
                            {'range': [80, 100], 'color': "#55efc4"}]}))
            st.plotly_chart(fig, use_container_width=True)

        # Realistic Feedback Section
        st.subheader("💡 Improvement Roadmap")
        suggestions = []
        if cgpa < 8.0: suggestions.append("📈 Focus on improving your academic CGPA above 8.0 for better eligibility.")
        if aptitude < 80: suggestions.append("🧠 Practice more quantitative and logical reasoning problems.")
        if coding < 75: suggestions.append("💻 Dedicate 1-2 hours daily to competitive coding on LeetCode/HackerRank.")
        if projects < 3: suggestions.append("🛠️ Build at least 1-2 more end-to-end projects to showcase your skills.")
        if comms < 7: suggestions.append("🗣️ Participate in mock interviews and GDs to improve communication.")
        
        if suggestions:
            for s in suggestions:
                st.info(s)
        else:
            st.success("🌟 Your profile looks strong! Keep maintaining this consistency.")

def show_resume_analyzer():
    from utils.resume_parser import extract_text_from_pdf, analyze_resume
    st.title("📄 Resume AI Analyzer")
    st.write("Upload your resume in PDF format to get an ATS score and improvement suggestions.")
    
    job_desc = st.text_area("Paste the Job Description (optional)", placeholder="e.g. We are looking for a Python developer with experience in SQL and Flask...", height=150)
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner("Analyzing resume..."):
            text = extract_text_from_pdf(uploaded_file)
            analysis = analyze_resume(text, job_desc)
            
            st.markdown(f"""
            <div class="card">
                <h3 style='color: #6c5ce7;'>Resume Analysis Result</h3>
                <div style='display: flex; justify-content: space-between;'>
                    <div>
                        <p style='font-size: 1.2em; font-weight: bold;'>ATS Score: {analysis['score']}/100</p>
                        <p>Word Count: {analysis['word_count']}</p>
                    </div>
                    {f"<div style='text-align: right;'><p style='font-size: 1.2em; font-weight: bold; color: #00b894;'>JD Match: {analysis['jd_score']}%</p><p>{analysis['jd_details']}</p></div>" if analysis['jd_score'] is not None else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Skills Found")
                st.write(", ".join(analysis['found_skills']) if analysis['found_skills'] else "No matching skills found.")
            with col2:
                st.subheader("Missing Skills (Recommended)")
                for skill in analysis['missing_skills']:
                    st.write(f"🔴 {skill}")
            
            st.info("💡 Tip: Add more keywords related to the job description to improve your score.")

def show_quiz():
    st.title("📝 Aptitude Quiz System")
    st.write("Test your skills across different categories.")
    
    category = st.selectbox("Select Category", list(QUIZ_DATA.keys()))
    
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'current_questions' not in st.session_state:
        st.session_state.current_questions = []

    if not st.session_state.quiz_started:
        if st.button("Start Quiz"):
            st.session_state.quiz_started = True
            st.session_state.current_questions = QUIZ_DATA[category]
            st.rerun()
    else:
        st.markdown(f"### {category}")
        user_answers = []
        for i, q in enumerate(st.session_state.current_questions):
            ans = st.radio(f"{i+1}. {q['question']}", q['options'], key=f"q_{i}")
            user_answers.append(ans)
        
        if st.button("Submit Quiz"):
            score = 0
            st.markdown("### 📊 Quiz Results")
            for i, q in enumerate(st.session_state.current_questions):
                if user_answers[i] == q['answer']:
                    score += 1
                    st.success(f"Question {i+1}: Correct! ✅")
                else:
                    st.error(f"Question {i+1}: Incorrect. ❌ Expected '{q['answer']}', but you chose '{user_answers[i]}'")
            
            final_score = int((score / len(st.session_state.current_questions)) * 100)
            save_quiz_score(st.session_state.user['id'], category, final_score, 100)
            
            st.subheader(f"Final Score: {final_score}/100")
            st.session_state.quiz_started = False
            if st.button("Finish & Go to Dashboard"):
                st.rerun()

def show_resources():
    st.title("📚 Career Preparation Resources")
    st.write("Handpicked resources and interview prep guides.")
    
    tab1, tab2 = st.tabs(["🚀 External Resources", "🎓 Viva & Interview Prep"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("🚀 Top Coding Platforms", expanded=True):
                st.markdown("""
                    - **[LeetCode](https://leetcode.com)** - Best for Algorithms & Data Structures.
                    - **[GeeksforGeeks](https://www.geeksforgeeks.org)** - Comprehensive CS theory and practice.
                    - **[HackerRank](https://www.hackerrank.com)** - Great for practicing language-specific skills.
                """)
            
            with st.expander("📺 Best YouTube Channels"):
                st.markdown("""
                    - **Striver (takeUforward)** - Amazing placement series.
                    - **CodeWithHarry** - Great for quick learning of any tech.
                    - **Love Babbar** - Very popular for DSA sheets.
                    - **Gate Smashers** - Best for core CS subjects (OS, DBMS, CN).
                """)

        with col2:
            with st.expander("📝 Resume & Portfolio"):
                st.markdown("""
                    - **[Canva](https://www.canva.com)** - Professional resume templates.
                    - **[Overleaf (LaTeX)](https://www.overleaf.com)** - Standard for high-end technical resumes.
                    - **[GitHub Pages](https://pages.github.com)** - Host your portfolio for free.
                """)
                
            with st.expander("🤝 Mock Interview Tools"):
                st.markdown("""
                    - **[Pramp](https://www.pramp.com)** - Practice peer-to-peer interviews.
                    - **[InterviewBit](https://www.interviewbit.com)** - Structured preparation path.
                """)

    with tab2:
        st.subheader("💡 Top 10 Technical Interview Questions")
        qa_pairs = [
            ("Q1: What is the difference between a List and a Tuple in Python?", "A: Lists are mutable (can be changed), while Tuples are immutable (cannot be changed after creation)."),
            ("Q2: What is the time complexity of a Binary Search?", "A: O(log n). It works by repeatedly dividing the search interval in half."),
            ("Q3: What are the four pillars of OOP?", "A: Encapsulation, Abstraction, Inheritance, and Polymorphism."),
            ("Q4: Explain the difference between INNER JOIN and LEFT JOIN.", "A: INNER JOIN returns only matching rows; LEFT JOIN returns all rows from the left table and matched rows from the right."),
            ("Q5: What is a deadlock in OS?", "A: A situation where two or more processes are blocked forever, each waiting for a resource held by another.")
        ]
        
        for q, a in qa_pairs:
            with st.expander(q):
                st.write(a)
                
        st.markdown("---")
        st.subheader("👨‍💼 HR & Behavioral Questions")
        st.info("**Tip:** Use the **STAR** method (Situation, Task, Action, Result) for behavioral answers.")
        with st.expander("Tell me about yourself."):
            st.write("Focus on your academic background, 2-3 key technical skills, and your best project (like PlaceMentor AI!).")
        with st.expander("What are your strengths and weaknesses?"):
            st.write("Strength: Problem-solving and quick learning. Weakness: Sometimes I focus too much on details, but I'm learning to manage time better using checklists.")

    st.info("💡 Pro Tip: Don't try to learn everything at once. Pick one language (like Python or Java) and master its Data Structures first.")

def show_coding_tracker():
    st.title("💻 Coding Practice Tracker")
    st.write("Log your daily coding progress and track consistency.")
    
    with st.form("coding_form"):
        platform = st.selectbox("Platform", ["LeetCode", "HackerRank", "CodeChef", "GeeksforGeeks", "Other"])
        problems = st.number_input("Problems Solved", 1, 50, 1)
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"])
        if st.form_submit_button("Log Progress"):
            save_coding_progress(st.session_state.user['id'], platform, problems, difficulty)
            st.success(f"Successfully logged {problems} {difficulty} problems on {platform}!")

    st.markdown("---")
    st.subheader("🌐 NEURAL BRIDGE: DIRECT PLATFORM ACCESS")
    st.markdown("""
        <div style='background: rgba(108, 92, 231, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #6c5ce7; margin-bottom: 20px;'>
            <p style='margin: 0; font-size: 0.9em; color: #2d3436;'>
                <b>SYNC PROTOCOL:</b> Launch your preferred coding environment below. We recommend keeping your <b>Username/ID</b> handy for a seamless transition.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    p_cols = st.columns(4)
    platforms = {
        "LeetCode": "https://leetcode.com/login/",
        "HackerRank": "https://www.hackerrank.com/auth/login",
        "CodeChef": "https://www.codechef.com/login",
        "GeeksforGeeks": "https://auth.geeksforgeeks.org/"
    }
    
    for i, (p_name, p_url) in enumerate(platforms.items()):
        with p_cols[i % 4]:
            st.link_button(f"🔗 {p_name.upper()}", p_url, use_container_width=True)

    with st.expander("📝 PLATFORM CREDENTIALS REFERENCE (OPTIONAL)"):
        st.caption("Store your platform usernames here for quick reference. (Note: Never store passwords!)")
        lc_user = st.text_input("LeetCode Username", placeholder="e.g. sudheer_2026")
        hr_user = st.text_input("HackerRank ID", placeholder="e.g. badam_sudheer")
        cc_user = st.text_input("CodeChef Handle", placeholder="e.g. placement_pro")
        
        if lc_user:
            if st.button("🚀 SYNC LEETCODE LIVE DATA"):
                with st.spinner("📡 Establishing Neural Link with LeetCode..."):
                    result = sync_leetcode_stats(lc_user)
                    if result["success"]:
                        st.balloons()
                        st.success(f"LIVE SYNC SUCCESSFUL: {result['totalSolved']} Problems Found!")
                        st.json({
                            "Total Solved": result["totalSolved"],
                            "Easy": result["easy"],
                            "Medium": result["medium"],
                            "Hard": result["hard"],
                            "Global Ranking": result["ranking"]
                        })
                        # Log to database as a bulk update
                        save_coding_progress(st.session_state.user['id'], "LeetCode (Live Sync)", result["totalSolved"], "Dynamic")
                    else:
                        st.error("Neural link failed. Verify your username and try again.")
        
        st.info("💡 These handles are used for real-time synchronization and quick reference.")

def show_skill_tracker():
    st.title("📊 Skill Matrix")
    st.write("Track and update your technical proficiency.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Add / Update Skill")
        with st.form("skill_form"):
            skill_name = st.text_input("Skill Name (e.g. Python, SQL)")
            proficiency = st.slider("Proficiency Level", 0, 100, 50)
            if st.form_submit_button("Save Skill"):
                if skill_name:
                    save_skill(st.session_state.user['id'], skill_name, proficiency)
                    st.success(f"Updated {skill_name}!")
                else:
                    st.error("Please enter a skill name")
    
    with col2:
        st.subheader("Your Skills")
        user_skills = get_user_skills(st.session_state.user['id'])
        if user_skills:
            for skill, level in user_skills:
                st.write(f"**{skill}**")
                st.progress(level / 100)
        else:
            st.info("No skills added yet.")

def show_support():
    st.title("📞 Support & Feedback")
    st.write("Have a question or found a bug? Reach out to the developer directly.")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown("""
            <div class='card' style='border-top: 8px solid #6c5ce7;'>
                <h3 class='rainbow-text' style='margin-bottom: 15px;'>Contact Developer</h3>
                <p class='rainbow-text'><b>Name:</b> BADAM SUDHEER REDDY</p>
                <p class='rainbow-text'><b>ID:</b> 2300033278</p>
                <p class='rainbow-text'><b>Email:</b> badamsudheerreddy@gmail.com</p>
                <p class='rainbow-text'><b>WhatsApp:</b> +91 8688509699</p>
                <hr style='border: 0.5px solid #eee;'>
                <p class='rainbow-text' style='font-weight: bold; margin-bottom: 5px;'>⏰ Support Availability:</p>
                <p class='rainbow-text' style='margin: 0; font-size: 0.9em;'><b>Mon - Sat:</b> 09:00 AM - 11:00 PM</p>
                <p style='margin: 0; font-size: 0.9em; color: #ff7675;'><i>*Times vary on Festivals & Important days</i></p>
                <p class='rainbow-text' style='font-size: 0.9em; margin-top: 10px;'>Feel free to reach out for project collaboration or technical support.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📩 Send Feedback / Bug Report")
        with st.form("feedback_form"):
            subject = st.selectbox("Topic", ["Bug Report", "Feature Request", "General Feedback", "Placement Help"])
            message = st.text_area("Details", placeholder="Describe your issue or suggestion here...")
            if st.form_submit_button("Submit Feedback"):
                if message:
                    send_feedback(st.session_state.user['id'], subject, message)
                    st.success("Thank you! Your feedback has been sent to Sudheer Reddy.")
                else:
                    st.error("Please enter a message.")

def show_settings():
    st.title("⚙️ Settings")
    
    current_user = st.session_state.user.get('username', '').upper()
    is_developer = current_user == 'BADAM SUDHEER REDDY'

    if is_developer:
        tab1, tab2, tab3 = st.tabs(["👤 Profile", "👨‍💻 Developer Console", "🛡️ Security Center"])
    else:
        tab1, tab3 = st.tabs(["👤 Profile", "🛡️ Security Center"])
    
    with tab1:
        st.write("Manage your account and preferences.")
        st.text_input("Change Username", value=st.session_state.user['username'])
        st.selectbox("Preferred Theme", ["Light", "Dark", "System Default"])
        if st.button("Update Profile"):
            st.success("Profile updated successfully!")
            
    with tab3:
        st.subheader("Your Security Activity")
        st.write("Review recent login attempts to keep your account safe.")
        logs = get_security_logs(st.session_state.user['id'])
        if logs:
            for ip, status, date in logs:
                icon = "✅" if status == "Success" else "⚠️"
                color = "green" if status == "Success" else "red"
                st.markdown(f"**{icon} {status}** from IP: `{ip}` at *{date}*")
        else:
            st.write("No activity logs available.")
        
        st.markdown("---")
        st.info("💡 **Security Tip:** Use a mix of symbols, numbers, and uppercase letters for a stronger password.")
    
    if is_developer:
        with tab2:
            st.subheader("Developer Control")
            st.info("This section is only for the developer to manage campus-wide updates.")
        
        # Post Notice
        with st.expander("📢 Post New Campus Notice", expanded=True):
            notice_text = st.text_area("Notice Content", placeholder="e.g. TCS Ninja Drive starting from Monday...")
            if st.button("Broadcast Notice"):
                if notice_text:
                    post_notice(notice_text)
                    st.success("Notice broadcasted to all students!")
                else:
                    st.error("Please enter notice content.")
        
        # View Feedback
        with st.expander("📩 View User Feedback"):
            feedbacks = get_all_feedback()
            if feedbacks:
                for user, sub, msg, date in feedbacks:
                    st.markdown(f"**From: {user}** ({date})")
                    st.info(f"**{sub}**: {msg}")
                    st.markdown("---")
            else:
                st.write("No user feedback received yet.")
        
        # All User Stats
        with st.expander("📊 All User Statistics & Performance"):
            user_data = get_all_user_stats()
            if user_data:
                df = pd.DataFrame(user_data, columns=["Username", "Email", "Last Active", "Problems", "Avg Quiz", "Skills"])
                # Calculate a mock readiness for the admin table
                df["Readiness %"] = (df["Skills"] * 8) + (df["Problems"] * 2)
                df["Readiness %"] = df["Readiness %"].apply(lambda x: min(100, x))
                st.dataframe(df, use_container_width=True)
                st.download_button("Download Report (.csv)", df.to_csv(index=False), "user_stats.csv", "text/csv")
            else:
                st.write("No user data available.")

import pandas as pd
if __name__ == "__main__":
    main()
