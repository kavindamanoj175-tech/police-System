import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති සැකසුම් (Page Configuration) ---
# මෙතනින් තමයි Browser එකේ Icon එක (Favicon) සහ නම හදන්නේ
st.set_page_config(
    page_title="STF Data Reporting - Jaffna & Vavuniya",
    page_icon="👮", # මෙය Favicon Icon එකයි. පසුව JSON file එකකින් මෙය වෙනස් කළ හැක
    layout="wide"
)

# --- 2. පද්ධති ආරක්ෂක කාර්යයන් (Security Functions) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS userstable
                 (username TEXT, password TEXT, is_approved INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_stats 
                 (date TEXT, zone TEXT, division TEXT, camp TEXT, 
                  SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS raids 
                 (date TEXT, zone TEXT, division TEXT, camp TEXT, raid_count INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS criminals 
                 (name TEXT, address TEXT, nic TEXT, phone TEXT, records TEXT, photo BLOB, camp TEXT)''")
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username,password,is_approved) VALUES (?,?,0)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password =? AND is_approved = 1', (username, password))
    data = c.fetchall()
    return data

def get_pending_users():
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT username FROM userstable WHERE is_approved = 0')
    return c.fetchall()

def approve_user(username):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('UPDATE userstable SET is_approved = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Database එක මුලින්ම සකස් කිරීම
init_db()

# --- 3. ධුරාවලිය (Hierarchy Data) ---
# (කලින් කෝඩ් එකේ තිබුණු Hierarchy data එක මෙතනට එයි. කෝඩ් එක දිග වැඩි නිසා මම කොටසක් විතරක් දානවා)
hierarchy = {
    "යාපනය කලාපය": {
        "යාපනය සේනාංකය": {
            "වි.කා.බ යාපනය කදවුර": [],
            "වි.කා.බ නෙල්ලිඅඩි කදවුර": ["වි.කා.බ කුඩත්තනේ උප කදවුර"]
        }
    }
}

# --- 4. Sidebar - ලෝගෝ සහ Admin පාලනය ---
# මචං, මෙතනින් තමයි ලෝගෝ එක සයිඩ් බාර් එකේ පෙන්වන්නේ
try:
    # 'logo.png' නමින් GitHub එකේ ඇති පින්තූරය ලෝඩ් කිරීම
    img = Image.open("logo.png")
    # පින්තූරය සයිඩ් බාර් එකේ පෙන්වීම (width එක adjust කරගන්න පුළුවන්)
    st.sidebar.image(img, use_column_width=True)
except FileNotFoundError:
    # පින්තූරය නැත්නම් text එකක් පෙන්වයි
    st.sidebar.error("Logo file (logo.png) not found in GitHub repository!")
exceptException as e:
    # වෙනත් දෝෂයක් ආවොත් පෙන්වයි
    st.sidebar.error(f"Error loading logo: {e}")

st.sidebar.divider()
st.sidebar.title("🛡️ පද්ධති ආරක්ෂාව")

# --- (මෙතැන් සිට කලින් තිබූ Login Logic එක ක්‍රියාත්මක වේ) ---
# Admin Panel (ඔයාට විතරක් ඇතුල් වෙන්න පුළුවන් රහස් තැන)
st.sidebar.subheader("👑 Admin පාලක පුවරුව")
admin_key = st.sidebar.text_input("Admin Key", type="password", help="අලුත් අය Approve කිරීමට රහස් කේතය ඇතුළත් කරන්න")

# (අර Admin Key සහ Login Logic ටික කලින් කෝඩ් එකේ තිබුණු විදිහටම තියෙයි)
# ...

# --- 5. ප්‍රධාන පද්ධතිය (ලොග් වුණු අයට පමණි) ---
if st.session_state.get('logged_in'):
    # ප්‍රධාන Heading එක
    st.title("🚨 Sri Lanka Police STF - Jaffna & Vavuniya Zones")
    st.subheader(f"📊 දත්ත වාර්තාකරණ පද්ධතිය (Data Reporting System) - සාදරයෙන් පිළිගනිමු {st.session_state['username']}!")
    st.divider()

    # Tabs (භට පිරිස්, වැටලීම්, etc.)
    # (කලින් කෝඩ් එකේ තිබුණු Logic ටික කලින් විදිහටම ක්‍රියාත්මක වේ)
    # ...

else:
    # ලොග් වෙන්න කලින් Heading එක
    st.markdown("## Sri Lanka Police Special Task Force")
    st.warning("⚠️ පද්ධතියට ඇතුළු වීමට ප්‍රථම ලොග් වන්න.")
    st.info("ඔබ නවකයෙකු නම් Sign Up වී Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")
