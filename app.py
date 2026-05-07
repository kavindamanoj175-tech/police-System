import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image
import io
import plotly.express as px

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Strategic Data System",
    page_icon="👮",
    layout="wide"
)

# --- 2. Database Init (ආරක්ෂිතව අලුත් Columns එකතු කිරීම) ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, tablet REAL, illegal_liquor REAL, goda REAL, sand REAL, wood REAL,
                  suspects INTEGER, suspect_name TEXT, other_records TEXT, location TEXT, court_date TEXT, case_no TEXT, 
                  image_blob BLOB, lat REAL, lon REAL)''')
    c.execute('CREATE TABLE IF NOT EXISTS force_details (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT, category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS intel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, info TEXT, priority TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS weapon_inv (id INTEGER PRIMARY KEY AUTOINCREMENT, weapon_type TEXT, amunition_count INTEGER, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS duty_roster (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, officer_name TEXT, duty_type TEXT, location TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 3. ධුරාවලිය (Hierarchy) - උඹේ පරණ එක ඒ විදිහටමයි ---
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

# --- 4. Sidebar LOGIN / SIGNUP ---
st.sidebar.title("👮 STF LOGIN")
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

menu = ["Login", "SignUp"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "SignUp":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("Sign Up"):
        conn = sqlite3.connect('police_master_system.db')
        c = conn.cursor()
        c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (new_user, new_password))
        conn.commit()
        st.success("Account Created! Please Login.")

elif choice == "Login":
    user = st.sidebar.text_input("User Name")
    passwd = st.sidebar.text_input("Password", type='password')
    if st.sidebar.checkbox("Login"):
        # සරල Login එකක් (සත්‍ය පද්ධතියකදී password hash පරීක්ෂා කළ යුතුය)
        st.session_state['logged_in'] = True
        st.sidebar.success(f"Welcome {user}")

# --- 5. Main App Logic ---
if st.session_state['logged_in']:
    tabs_list = ["📝 වැටලීම්", "📉 භට පිරිස්", "🔍 වාර්තා", "📊 සාරාංශ/Maps", "🔫 අවි ආයුධ", "📅 රාජකාරි", "🕵️ Intel"]
    
    # Navigation Buttons (පරණ විදිහටම)
    col_h1, col_h2, col_h3 = st.sidebar.columns(3)
    if col_h1.button("🏠 Home"): st.session_state['tab_idx'] = 0
    
    # Sidebar Selections
    zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
    div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
    main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
    sub_camp = st.sidebar.selectbox("ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])
    
    admin_key = st.sidebar.text_input("Admin Key", type="password")
    is_admin = (admin_key == "Police@123")

    # Tabs Display
    sel_tab = st.tabs(tabs_list)

    # --- TAB 1: RAID ENTRY ---
    with sel_tab[0]:
        st.subheader(f"📝 වැටලීම් වාර්තාව - {sub_camp}")
        with st.form("raid_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0)
            k_ganja = c2.number_input("කේරළ ගංජා (ග්‍රෑම්)", 0.0)
            heroin = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0)
            tablet = c4.number_input("මත් කරල්", 0.0)
            liq = c1.number_input("මත්පැන් (මි.ලී)", 0.0)
            goda = c2.number_input("ගෝඩා (ලීටර්)", 0.0)
            sand = c3.number_input("වැලි වැටලීම්", 0.0)
            wood = c4.number_input("දැව වැටලීම්", 0.0)
            
            s_name = st.text_input("සැකකරුගේ නම")
            location = st.text_input("ස්ථානය (ගම/GPS)")
            lat = st.number_input("Latitude", format="%.6f", value=6.9271)
            lon = st.number_input("Longitude", format="%.6f", value=79.8612)
            other_txt = st.text_area("අමතර සටහන්")
            uploaded_file = st.file_uploader("සාක්ෂි ඡායාරූප", type=['jpg', 'png'])

            if st.form_submit_button("දත්ත සුරකින්න"):
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, tablet, illegal_liquor, goda, sand, wood, suspects, suspect_name, other_records, location, lat, lon) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, tablet, liq, goda, sand, wood, 1 if s_name else 0, s_name, other_txt, location, lat, lon))
                conn.commit(); conn.close(); st.success("සාර්ථකව සුරැකිණි!")

    # --- TAB 2: FORCE DETAILS ---
    with sel_tab[1]:
        st.subheader(f"📉 භට පිරිස් දත්ත - {sub_camp}")
        with st.form("force_form"):
            f1, f2, f3 = st.columns(3)
            ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); pc = f3.number_input("PC", 0)
            if pc < 5 and pc > 0: st.error("⚠️ අවධානයට: PC සංඛ්‍යාව අවම මට්ටමක පවතී!")
            if st.form_submit_button("Update Force Data"):
                st.success("දත්ත යාවත්කාලීන විය!")

    # --- TAB 3: RECORDS ---
    with sel_tab[2]:
        st.subheader("🔍 වාර්තා පිරික්සුම")
        conn = sqlite3.connect('police_master_system.db')
        df = pd.read_sql_query("SELECT * FROM detailed_raids", conn)
        st.dataframe(df.drop(columns=['image_blob'], errors='ignore'))
        conn.close()

    # --- TAB 4: MAPS ---
    with sel_tab[3]:
        st.subheader("📍 වැටලීම් සිතියම")
        conn = sqlite3.connect('police_master_system.db')
        df_map = pd.read_sql_query("SELECT lat, lon, suspect_name FROM detailed_raids", conn)
        if not df_map.empty: st.map(df_map)
        conn.close()

    # --- TAB 7: INTEL (ADMIN ONLY) ---
    with sel_tab[6]:
        if is_admin:
            st.subheader("🕵️ Secret Intelligence Log")
            intel_txt = st.text_area("රහසිගත තොරතුර")
            if st.button("Log Info"): st.success("Logged!")
        else:
            st.warning("මෙම ටැබ් එක බැලීමට නිවැරදි Admin Key එක ඇතුළත් කරන්න.")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
else:
    st.info("කරුණාකර Sidebar එකෙන් Login වන්න හෝ Signup වන්න.")
