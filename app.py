import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image
import plotly.express as px

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(page_title="STF - Strategic Data System", page_icon="👮", layout="wide")

# --- 2. Database Init (Updated with Status Column) ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    # status: 'pending' or 'approved'
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT PRIMARY KEY, password TEXT, status TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, tablet REAL, illegal_liquor REAL, goda REAL, sand REAL, wood REAL,
                  suspects INTEGER, suspect_name TEXT, other_records TEXT, location TEXT, court_date TEXT, case_no TEXT, 
                  image_blob BLOB, lat REAL, lon REAL)''')
    c.execute('CREATE TABLE IF NOT EXISTS force_details (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT, category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS intel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, info TEXT, priority TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS vehicle_log (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_no TEXT, status TEXT, last_service TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 3. ධුරාවලිය (Hierarchy) - උඹේ පරණ ලිස්ට් එකමයි ---
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
    },
    "වව්නියාව කලාපය": {
        "වව්නියාව සේනාංකය": {
            "වි.කා.බ වව්නියාව කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ අනුරාධපුර කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ කැබිතිගොල්ලෑව කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ සෙට්ටිකුලම් කදවුර": ["ප්‍රධාන කදවුර"]
        },
        "ත්‍රිකුණාමලය සේනාංකය": {
            "වි.කා.බ ත්‍රිකුණාමලය කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ වාකරේ කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ කන්තලේ කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ පුල්මුඩේ කදවුර": ["ප්‍රධාන කදවුර"]
        }
    }
}

# --- 4. Sidebar Access & Admin Logic ---
st.sidebar.title("👮 STF Access Control")
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

menu = ["Login", "SignUp", "Admin Settings"]
choice = st.sidebar.selectbox("Menu", menu)

# --- SIGNUP LOGIC ---
if choice == "SignUp":
    st.subheader("නව ගිණුමක් සාදන්න (Approval අවශ්‍ය වේ)")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type='password')
    if st.button("ගිණුම සාදන්න"):
        conn = sqlite3.connect('police_master_system.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO userstable(username, password, status) VALUES (?,?,?)', (new_user, new_pass, 'pending'))
            conn.commit()
            st.success("ලියාපදිංචිය සාර්ථකයි! Admin අනුමත කළ පසු ඔබට Login විය හැක.")
        except: st.error("මෙම නම දැනටමත් ඇත.")
        conn.close()

# --- LOGIN LOGIC ---
elif choice == "Login":
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.checkbox("Login"):
        conn = sqlite3.connect('police_master_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, p))
        res = c.fetchone()
        if res:
            if res[2] == 'approved':
                st.session_state['logged_in'] = True
                st.session_state['user'] = u
                st.sidebar.success(f"Welcome {u}")
            else: st.warning("ඔබේ ගිණුම තවමත් අනුමත කර නැත.")
        else: st.error("වැරදි දත්ත!")
        conn.close()

# --- ADMIN USER MANAGEMENT ---
elif choice == "Admin Settings":
    st.subheader("පරිශීලක අනුමැතිය සහ කළමනාකරණය")
    key = st.text_input("Admin Key", type="password")
    if key == "Police@123":
        conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
        users = pd.read_sql_query("SELECT username, status FROM userstable", conn)
        st.table(users)
        u_to_app = st.selectbox("අනුමත කිරීමට නම තෝරන්න", users[users['status']=='pending']['username'].tolist() if not users[users['status']=='pending'].empty else ["දත්ත නැත"])
        if st.button("Approve User"):
            c.execute("UPDATE userstable SET status='approved' WHERE username=?", (u_to_app,))
            conn.commit(); st.success("අනුමත කළා!"); st.rerun()
        conn.close()

# --- 5. Main Content (Login වුණු අයට පමණයි) ---
if st.session_state['logged_in']:
    # පරණ ටැබ් ලිස්ට් එකට සිතියම් එකතු කළා
    tabs_list = ["📝 වැටලීම්", "📉 භට පිරිස්", "🔍 වාර්තා", "🗺️ සිතියම/සාරාංශ", "🚔 වාහන", "🕵️ Intel"]
    sel_tab = st.tabs(tabs_list)

    # Sidebar Selections (පරණ විදිහටම)
    zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
    div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
    sub_camp = st.sidebar.selectbox("ස්ථානය", list(hierarchy[zone_sel][div_sel].keys()))
    admin_key = st.sidebar.text_input("Admin Secret Key", type="password")
    is_admin = (admin_key == "Police@123")

    # --- TAB 1: RAID ENTRY (Suspect History එකතු කළා) ---
    with sel_tab[0]:
        st.subheader(f"වැටලීම් වාර්තාව - {sub_camp}")
        with st.form("raid_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0)
            k_ganja = c2.number_input("කේරළ ගංජා (ග්‍රෑම්)", 0.0)
            heroin = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0)
            tablet = c4.number_input("මත් කරල්", 0.0)
            
            s_name = st.text_input("සැකකරුගේ නම (සම්පූර්ණ නම)")
            # Suspect Checker
            if s_name:
                conn = sqlite3.connect('police_master_system.db')
                check = pd.read_sql_query(f"SELECT date, location FROM detailed_raids WHERE suspect_name LIKE '%{s_name}%'", conn)
                if not check.empty: st.warning(f"⚠️ මොහු මීට පෙර {len(check)} වතාවක් හසුවී ඇත!")
                conn.close()

            location = st.text_input("ස්ථානය (ගම/GPS)")
            lat = st.number_input("Latitude", format="%.6f", value=6.9271)
            lon = st.number_input("Longitude", format="%.6f", value=79.8612)
            
            if st.form_submit_button("දත්ත සුරකින්න"):
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, tablet, suspect_name, location, lat, lon) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, tablet, s_name, location, lat, lon))
                conn.commit(); conn.close(); st.success("දත්ත සුරැකිණි!")

    # --- TAB 4: MAP & ANALYTICS ---
    with sel_tab[3]:
        st.subheader("📍 වැටලීම් සිතියම")
        conn = sqlite3.connect('police_master_system.db')
        df_map = pd.read_sql_query("SELECT lat, lon, suspect_name, location FROM detailed_raids", conn)
        if not df_map.empty: st.map(df_map)
        
        # Summary Graph
        df_r = pd.read_sql_query("SELECT ice, kerala_ganja, heroin FROM detailed_raids", conn)
        if not df_r.empty:
            fig = px.bar(df_r.sum().reset_index(), x='index', y=0, title="මත්ද්‍රව්‍ය ප්‍රමාණයන්")
            st.plotly_chart(fig)
        conn.close()

    # --- TAB 6: INTEL (ADMIN ONLY) ---
    with sel_tab[5]:
        if is_admin:
            st.subheader("🕵️ Intelligence Log")
            st.table(pd.read_sql_query("SELECT * FROM intel_log", sqlite3.connect('police_master_system.db')))
        else: st.warning("Admin Key එක ඇතුළත් කරන්න.")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False; st.rerun()
else:
    st.info("Sidebar එකෙන් Login වන්න හෝ අලුත් ගිණුමක් (SignUp) සාදා ගන්න.")
