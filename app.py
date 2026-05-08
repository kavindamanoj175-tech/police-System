import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import io

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(page_title="STF - Security Data Management", page_icon="👮", layout="wide")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    # UserTable එකට 'role' එකතු කළා
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT, role TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mandrax REAL, 
                  illegal_liquor REAL, goda REAL, sand_timber REAL, suspects INTEGER, other_records TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  vehicle_no TEXT, vehicle_type TEXT, service_type TEXT, service_station TEXT, 
                  repair_loc TEXT, repair_details TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def login_user(username, password):
    with sqlite3.connect('police_master_system.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (username, password))
        return c.fetchone()

init_db()

# --- 3. Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['role'] = 'User'

def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT, role TEXT)')
    
    # පරණ Table එකට 'role' කියන කොටස බලෙන්ම ඇතුල් කිරීමට (Alter Table):
    try:
        c.execute('ALTER TABLE userstable ADD COLUMN role TEXT DEFAULT "User"')
    except:
        pass # දැනටමත් තියෙනවා නම් Error එකක් නොදී ඉන්න
    
    # ... (අනිත් Tables ඒ විදිහටම තියෙන්න දෙන්න)
    conn.commit()
    conn.close()

# --- 4. Sidebar ---
st.sidebar.title("👮 STF DBMS - Admin Control")
sl_time = datetime.now() + timedelta(hours=5, minutes=30)
st.sidebar.markdown(f"📅 **{sl_time.strftime('%Y-%m-%d')}** | ⏰ **{sl_time.strftime('%H:%M:%S')}**")
st.sidebar.divider()

# --- 5. Login / Sign Up Logic ---
if not st.session_state['logged_in']:
    auth_mode = st.sidebar.selectbox("පද්ධතියට ඇතුල් වන්න", ["Login", "Sign Up"])
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    
    if auth_mode == "Login":
        if st.sidebar.button("Login"):
            res = login_user(u, make_hashes(p))
            if res:
                st.session_state['logged_in'] = True
                st.session_state['username'] = res[0]
                st.session_state['role'] = res[2] # Role එක මතක තබා ගනී
                st.rerun()
            else: st.sidebar.error("Username හෝ Password වැරදියි!")
    else:
        admin_key = st.sidebar.text_input("Admin Key (Account Creation)", type='password')
        if st.sidebar.button("ගිණුම සාදන්න"):
            role = "Admin" if admin_key == "Police@123" else "User"
            try:
                with sqlite3.connect('police_master_system.db') as conn:
                    conn.execute('INSERT INTO userstable(username, password, role) VALUES (?,?,?)', (u, make_hashes(p), role))
                st.sidebar.success(f"{u} ({role}) සාර්ථකයි! දැන් Login වන්න.")
            except: st.sidebar.error("ගිණුම සෑදීමේ ගැටලුවක්!")
    st.stop()

# --- 6. Content (After Login) ---
st.sidebar.write(f"Logged in as: **{st.session_state['username']}** ({st.session_state['role']})")

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

zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- Tabs ---
tabs_list = ["📝 වැටලීම්", "📉 භට පිරිස්", "🚔 වාහන", "🔍 වාර්තා", "📊 විශ්ලේෂණය"]
current_tab = st.radio("ප්‍රධාන මෙනුව", tabs_list, horizontal=True)

def get_db(): return sqlite3.connect('police_master_system.db')

# (පැරණි Raid Entry සහ Force Details කෝඩ් එක මෙතන තියෙනවා - කෙටි කළේ ඉඩ ඉතිරි කරගන්නයි)
if current_tab == "📝 වැටලීම්":
    st.subheader(f"වැටලීම් - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0); kg = c2.number_input("කේරළ ගංජා (කිග්‍රෑ)", 0.0)
        hr = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0); mx = c4.number_input("මද්‍රාස් (ග්‍රෑම්)", 0.0)
        liq = c1.number_input("මත්පැන් (ml)", 0.0); gd = c2.number_input("ගෝඩා (L)", 0.0)
        stmb = c3.number_input("වැලි/දැව වැටලීම්", 0.0); sus = c4.number_input("සැකකරුවන්", 0)
        info = st.text_area("විශේෂ සටහන්")
        if st.form_submit_button("දත්ත සුරකින්න"):
            with get_db() as conn:
                conn.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mandrax, illegal_liquor, goda, sand_timber, suspects, other_records) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (sl_time.strftime("%Y-%m-%d"), sl_time.strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, kg, hr, mx, liq, gd, stmb, sus, info))
            st.success("සාර්ථකයි!")

elif current_tab == "📉 භට පිරිස්":
    st.subheader(f"භට පිරිස් - {sub_camp}")
    with st.form("force_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "විශේෂ රාජකාරි", "නිවාඩු/විවේක"])
        if st.form_submit_button("යාවත්කාලීන කරන්න"):
            with get_db() as conn:
                conn.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (sl_time.strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, (ssp+sp+asp+ci+ip+si+ps+pc)))
            st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")

elif current_tab == "🚔 වාහන":
    st.subheader(f"වාහන පාලනය - {sub_camp}")
    v_tab1, v_tab2 = st.tabs(["➕ ඇතුළත් කිරීම", "📋 ලේඛනය"])
    with v_tab1:
        with st.form("v_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            v_no = col1.text_input("වාහන අංකය")
            v_type = col1.selectbox("වාර්ගය", ["Land Rover", "Jeep", "Cab", "Truck", "Motorbike"])
            v_status = col2.selectbox("තත්ත්වය", ["ධාවනය කළ හැක", "අලුත්වැඩියාවට යවා ඇත", "ධාවනය කළ නොහැක"])
            v_info = col2.text_area("විස්තර")
            if st.form_submit_button("සුරකින්න"):
                with get_db() as conn:
                    conn.execute('INSERT INTO vehicle_records (date, zone, division, camp, vehicle_no, vehicle_type, status, repair_details) VALUES (?,?,?,?,?,?,?,?)',
                                 (sl_time.strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, v_no, v_type, v_status, v_info))
                st.success("වාහන දත්ත සුරැකිණි!")
    with v_tab2:
        conn = get_db()
        st.dataframe(pd.read_sql_query("SELECT * FROM vehicle_records WHERE zone=?", conn, params=(zone_sel,)))
        conn.close()

elif current_tab == "🔍 වාර්තා":
    st.subheader("🔍 දත්ත ගොනු")
    rep_type = st.selectbox("වර්ගය", ["detailed_raids", "force_details", "vehicle_records"])
    conn = get_db()
    df = pd.read_sql_query(f"SELECT * FROM {rep_type} WHERE zone=?", conn, params=(zone_sel,))
    
    if st.session_state['role'] == "Admin":
        st.warning("ඔබ Admin බැවින් දත්ත සංස්කරණය කළ හැක.")
        edited = st.data_editor(df, num_rows="dynamic")
        if st.button("වෙනස්කම් සුරකින්න"):
            edited.to_sql(rep_type, conn, if_exists='replace', index=False)
            st.success("දත්ත යාවත්කාලීන විය!")
    else:
        st.dataframe(df)
    conn.close()

elif current_tab == "📊 විශ්ලේෂණය":
    st.info("දත්ත විශ්ලේෂණ ප්‍රස්ථාර මෙහි පෙන්වයි.")
