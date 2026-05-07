import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති සැකසුම් ---
# මචං, මම මෙතන ඔයා ඉල්ලපු විදිහට Icon එක සහ Title එක අප්ඩේට් කළා
st.set_page_config(
    page_title="STF - Strategic Data Management",
    page_icon="👮",
    layout="wide"
)

# --- 2. පද්ධති ආරක්ෂක කාර්යයන් ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT, is_approved INTEGER DEFAULT 0)')
    # Raid table එකට තව දත්ත ඕන වෙලාවක දාන්න column එකක් (item_name, quantity) විදිහට වෙනස් කරන්න පුළුවන්
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  item_type TEXT, quantity REAL, suspects INTEGER, other_records TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER, row_total INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS system_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, note TEXT)''')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit(); conn.close()

def login_user(username, password):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password =? AND is_approved = 1', (username, password))
    return c.fetchall()

def approve_user(username):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('UPDATE userstable SET is_approved = 1 WHERE username = ?', (username,))
    conn.commit(); conn.close()

def get_pending_users():
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('SELECT username FROM userstable WHERE is_approved = 0')
    return c.fetchall()

init_db()

# --- 3. ධුරාවලිය (Hierarchy) ---
# මෙතන උප කදවුරු structure එක මම දියුණු කළා
hierarchy = {
    "යාපනය කලාපය": {
        "යාපනය සේනාංකය": {
            "වි.කා.බ යාපනය කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ නෙල්ලිඅඩි කදවුර": ["ප්‍රධාන කදවුර", "වි.කා.බ කුඩත්තනේ උප කදවුර"],
            "වි.කා.බ කිලිනොච්චිය කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ මුලතිව් කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ මාන්කුලම් කදවුර": ["ප්‍රධාන කදවුර", "වි.කා.බ පුලියන්කුලම් උප කදවුර"]
        },
        "මන්නාරම සේනාංකය": {
            "වි.කා.බ පුඅවරසන්කුලම්": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ පරයනාලන්කුලම්": ["ප්‍රධාන කදවුර", "වි.කා.බ මරිච්චීකට්ටී උප කදවුර"],
            "වි.කා.බ මන්නාරම": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ ඉලුප්පුකඩවායි": ["ප්‍රධාන කදවුර"]
        }
    }
}

# --- 4. Sidebar (Login & Signup) ---
st.sidebar.title("👮 STF DBMS")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    menu = ["Login", "SignUp"]
    choice = st.sidebar.selectbox("පද්ධතියට ඇතුළු වන්න", menu)
    if choice == "Login":
        u = st.sidebar.text_input("User Name")
        p = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            if login_user(u, check_hashes(p, make_hashes(p))):
                st.session_state['logged_in'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.sidebar.error("වැරදි දත්ත!")
    elif choice == "SignUp":
        new_u = st.sidebar.text_input("Username")
        new_p = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Create Account"):
            add_userdata(new_u, make_hashes(new_p))
            st.sidebar.success("අනුමැතිය සඳහා යොමු කළා.")
    st.stop()

# --- 5. Main System Layout ---
st.sidebar.divider()
zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp_sel = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp_sel = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp_sel])

# Admin Key check for edits
admin_key = st.sidebar.text_input("Admin Key (Security)", type="password")
is_admin = (admin_key == "Police@123")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🕵️ වැටලීම් ඇතුළත් කිරීම", "👮 භට පිරිස් දත්ත", "🔍 විස්තරාත්මක වාර්තා", "📊 සංඛ්‍යාත්මක විශ්ලේෂණය", "📝 සටහන් පොත"])

# --- TAB 1: Flexible Raid Entry ---
with tab1:
    st.subheader(f"වැටලීම් දත්ත ඇතුළත් කිරීම - {sub_camp_sel}")
    # ඔයා ඉල්ලපු විදිහට අලුත් දේවල් ඇඩ් කරගන්න පුළුවන් tool එක
    with st.form("raid_form_flexible", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item_type = col1.selectbox("වැටලීම් ද්‍රව්‍ය වර්ගය", ["අයිස් (ICE)", "කේරළ ගංජා", "හෙරොයින්", "නීතිවිරෝධී මත්පැන්", "වැලි", "ලී", "වෙනත්"])
        qty = col2.number_input("ප්‍රමාණය (ග්‍රෑම්/කිලෝ/ලීටර්/ගණන)", 0.0)
        suspects = col1.number_input("සැකකරුවන් ගණන", 0)
        other_info = st.text_area("අමතර විස්තර (වාහන අංක/ආයුධ ආදිය)")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            now = datetime.now()
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, item_type, quantity, suspects, other_records) 
                         VALUES (?,?,?,?,?,?,?,?,?)''', 
                      (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), zone_sel, div_sel, sub_camp_sel, item_type, qty, suspects, other_info))
            conn.commit(); conn.close(); st.success("දත්ත සාර්ථකව ඇතුළත් විය!")

# --- TAB 2: Dedicated Force Management ---
with tab2:
    st.subheader(f"භට පිරිස් දත්ත යාවත්කාලීන කිරීම - {sub_camp_sel}")
    # සියලුම යූසර්ස්ලාට ඇක්සස් දීලා තියෙන්නේ
    with st.form("force_form_main", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0); ci = f4.number_input("CI", 0)
        ip = f1.number_input("IP", 0); si = f2.number_input("SI", 0); ps = f3.number_input("PS", 0); psd = f4.number_input("PSD", 0)
        pc = f1.number_input("PC", 0); pcd = f2.number_input("PCD", 0)
        
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි පිටව ගොස් ඇති", "02 නිවාඩු/විවේක පිටව ගොස් ඇති"])
        
        if st.form_submit_button("භට පිරිස් වාර්තාව යාවත්කාලීන කරන්න"):
            tot = ssp+sp+asp+ci+ip+si+ps+psd+pc+pcd
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, row_total) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp_sel, cat, ssp, sp, asp, ci, ip, si, ps, psd, pc, pcd, tot))
            conn.commit(); conn.close(); st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")

# --- TAB 3: Advanced Reporting (Regional/Divisional) ---
with tab3:
    st.subheader("🔍 වාර්තා පිරික්සුම (Regional & Divisional)")
    view_mode = st.radio("දත්ත බැලිය යුතු මට්ටම", ["කලාප මට්ටමින්", "සේනාංක මට්ටමින්", "කදවුරු මට්ටමින්"], horizontal=True)
    
    conn = sqlite3.connect('police_master_system.db')
    if view_mode == "කලාප මට්ටමින්":
        q = f"SELECT * FROM detailed_raids WHERE zone='{zone_sel}'"
        fq = f"SELECT * FROM force_details WHERE zone='{zone_sel}'"
    elif view_mode == "සේනාංක මට්ටමින්":
        q = f"SELECT * FROM detailed_raids WHERE division='{div_sel}'"
        fq = f"SELECT * FROM force_details WHERE division='{div_sel}'"
    else:
        q = f"SELECT * FROM detailed_raids WHERE camp='{sub_camp_sel}'"
        fq = f"SELECT * FROM force_details WHERE camp='{sub_camp_sel}'"
    
    df_raids = pd.read_sql_query(q, conn)
    df_force = pd.read_sql_query(fq, conn)
    conn.close()

    col_r, col_f = st.columns(2)
    with col_r:
        st.write("🕵️ වැටලීම් ඉතිහාසය")
        st.dataframe(df_raids, use_container_width=True)
    with col_f:
        st.write("👮 භට පිරිස් ඉතිහාසය")
        st.dataframe(df_force, use_container_width=True)

# --- TAB 4: Analysis (Force Balance Sheet) ---
with tab4:
    st.subheader("📊 දෛනික භට පිරිස් ශේෂ පත්‍රය")
    # මෙතනදී Divisional reporting එක ඔයා ඉල්ලපු විදිහට auto-calculate වෙනවා
    if not df_force.empty:
        df_force['date'] = pd.to_datetime(df_force['date'])
        latest_date = df_force['date'].max()
        st.info(f"අවසන් වරට දත්ත යාවත්කාලීන වූ දිනය: {latest_date.date()}")
        
        # Summary calculation
        sum_df = df_force[df_force['date'] == latest_date].groupby('category')[['SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'row_total']].sum().reset_index()
        st.table(sum_df[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'row_total']])
        
        fig = px.pie(sum_df, values='row_total', names='category', title="භට පිරිස් ව්‍යාප්තිය")
        st.plotly_chart(fig)

# --- TAB 5: Notes & Admin Logout ---
with tab5:
    st.subheader("📝 පද්ධති සටහන්")
    note = st.text_area("වැදගත් පණිවිඩයක් ඇතුළත් කරන්න")
    if st.button("සටහන සුරකින්න"):
        conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
        c.execute('INSERT INTO system_notes (username, date, note) VALUES (?,?,?)', (st.session_state['username'], datetime.now().strftime("%Y-%m-%d"), note))
        conn.commit(); conn.close(); st.success("සටහන සුරැකිණි!")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
