import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF DBMS - Detailed Reporting",
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
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mava REAL, 
                  mandrax REAL, dambul REAL, illegal_liquor REAL, goda REAL,
                  unidentified_liquor REAL, gov_liquor REAL, sand_timber REAL,
                  tobacco REAL, cigarettes REAL, fireworks REAL, suspects INTEGER,
                  other_records TEXT)''')
    
    # නව භට පිරිස් දත්ත වගුව
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER, row_total INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS system_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, note TEXT)''')
    conn.commit()
    conn.close()

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

# --- 3. ධුරාවලිය (Hierarchy Data) ---
hierarchy = {
    "යාපනය කලාපය": {
        "යාපනය සේනාංකය": {
            "වි.කා.බ යාපනය කදවුර": [],
            "වි.කා.බ නෙල්ලිඅඩි කදවුර": ["වි.කා.බ කුඩත්තනේ උප කදවුර"],
            "වි.කා.බ කිලිනොච්චිය කදවුර": [],
            "වි.කා.බ මුලතිව් කදවුර": [],
            "වි.කා.බ මාන්කුලම් කදවුර": ["වි.කා.බ පුලියන්කුලම් උප කදවුර"]
        },
        "මන්නාරම සේනාංකය": {
            "වි.කා.බ පුඅවරසන්කුලම්": [],
            "වි.කා.බ පරයනාලන්කුලම්": ["වි.කා.බ මරිච්චීකට්ටී උප කදවුර"],
            "වි.කා.බ මන්නාරම": [],
            "වි.කා.බ ඉලුප්පුකඩවායි": []
        }
    },
    "වව්නියාව කලාපය": {
        "වව්නියාව සේනාංකය": {
            "වි.කා.බ වව්නියාව කදවුර": [],
            "වි.කා.බ අනුරාධපුර කදවුර": [],
            "වි.කා.බ කැබිතිගොල්ලෑව කදවුර": [],
            "වි.කා.බ සෙට්ටිකුලම් කදවුර": []
        },
        "ත්‍රිකුණාමලය සේනාංකය": {
            "වි.කා.බ ත්‍රිකුණාමලය කදවුර": [],
            "වි.කා.බ වාකරේ කදවුර": [],
            "වි.කා.බ කන්තලේ කදවුර": [],
            "වි.කා.බ පුල්මුඩේ කදවුර": []
        }
    }
}

# --- 4. Sidebar ---
st.sidebar.title("👮 STF DBMS")
try:
    img = Image.open("logo.png")
    st.sidebar.image(img, use_column_width=True)
except Exception:
    st.sidebar.info("Logo not found.")

st.sidebar.divider()
admin_key = st.sidebar.text_input("Admin Key", type="password")
is_admin = (admin_key == "Police@123")

if is_admin:
    st.sidebar.success("Admin Access: ON")
    pending = get_pending_users()
    if pending:
        u_to_app = st.sidebar.selectbox("Approve User", [u[0] for u in pending])
        if st.sidebar.button("Confirm Approval"):
            approve_user(u_to_app); st.sidebar.success("Approved!"); st.rerun()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        if login_user(u, check_hashes(p, make_hashes(p))):
            st.session_state['logged_in'] = True; st.session_state['username'] = u; st.rerun()
        else: st.sidebar.error("අනුමත කර නැත හෝ වැරදි දත්ත!")
    st.stop()

# --- 5. Main System ---
st.title("🚨 Special Task Force - Data Management System")

zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))

camps_list = []
for main_camp, sub_camps in hierarchy[zone_sel][div_sel].items():
    camps_list.append(main_camp)
    camps_list.extend(sub_camps)

camp_sel = st.sidebar.selectbox("කදවුර / උප කදවුර", camps_list)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "🔍 විස්තරාත්මක වාර්තා", "📊 සාරාංශ ගත වාර්තා", "📝 සටහන් පොත", "📉 භට පිරිස් වාර්තාව"])

# --- TAB 1: Data Entry ---
with tab1:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.header(f"🕵️ වැටලීම් දත්ත")
        with st.form("detailed_raid_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", min_value=0.0)
            k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", min_value=0.0)
            heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", min_value=0.0)
            mava = c1.number_input("මාවා (Mava) - කි.ග්‍රෑ", min_value=0.0)
            mandrax = c2.number_input("මැන්ඩ්‍රැක්ස් - පෙති", min_value=0.0)
            dambul = c3.number_input("ඩම්බුල් - කි.ග්‍රෑ", min_value=0.0)
            liq_ill = c1.number_input("නීතිවිරෝධී මත්පැන් (බෝතල්)", min_value=0.0)
            goda = c2.number_input("ගෝඩා (ලීටර්)", min_value=0.0)
            sand_timber = c3.number_input("වැලි/ලී වැටලීම්", min_value=0)
            suspects = c1.number_input("සැකකරුවන් ගණන", min_value=0)
            other_text = st.text_area("වෙනත් විස්තර")
            
            if st.form_submit_button("වාර්තාව සුරකින්න"):
                now = datetime.now()
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mava, mandrax, dambul, illegal_liquor, goda, sand_timber, suspects, other_records) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), zone_sel, div_sel, camp_sel, ice, k_ganja, heroin, mava, mandrax, dambul, liq_ill, goda, sand_timber, suspects, other_text))
                conn.commit(); conn.close(); st.success("දත්ත සුරැකිණි!")

    with col_b:
        st.header(f"👮 භට පිරිස් දත්ත")
        with st.form("force_entry_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            ssp = f1.number_input("SSP", min_value=0)
            sp = f2.number_input("SP", min_value=0)
            asp = f3.number_input("ASP", min_value=0)
            ci = f1.number_input("CI", min_value=0)
            ip = f2.number_input("IP", min_value=0)
            si = f3.number_input("SI", min_value=0)
            ps = f1.number_input("PS", min_value=0)
            psd = f2.number_input("PSD", min_value=0)
            pc = f3.number_input("PC", min_value=0)
            pcd = f1.number_input("PCD", min_value=0)
            
            category = st.selectbox("තෝරන්න", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි පිටව ගොස් ඇති", "02 රාජකාරි දින විවේකය පිටව ගොස් ඇති"])
            
            if st.form_submit_button("භට පිරිස් දත්ත සුරකින්න"):
                row_tot = ssp+sp+asp+ci+ip+si+ps+psd+pc+pcd
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, row_total) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, camp_sel, category, ssp, sp, asp, ci, ip, si, ps, psd, pc, pcd, row_tot))
                conn.commit(); conn.close(); st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")

# --- TAB 2 & 3 (Raid Reports & Analysis) ---
with tab2:
    st.header("🔍 වැටලීම් කළමනාකරණය")
    start_dt = st.date_input("ආරම්භය", value=datetime.now(), key="s1")
    end_dt = st.date_input("අවසානය", value=datetime.now(), key="e1")
    conn = sqlite3.connect('police_master_system.db')
    df = pd.read_sql_query(f"SELECT * FROM detailed_raids WHERE date BETWEEN '{start_dt}' AND '{end_dt}' AND camp='{camp_sel}'", conn)
    st.dataframe(df, use_container_width=True, hide_index=True)
    conn.close()

with tab3:
    st.header("📈 විශ්ලේෂණය")
    conn = sqlite3.connect('police_master_system.db')
    df_all = pd.read_sql_query("SELECT * FROM detailed_raids", conn)
    if not df_all.empty:
        st.plotly_chart(px.bar(df_all, x="zone", y="suspects", color="division", title="කලාපීය සැකකරුවන්"), use_container_width=True)
    conn.close()

# --- TAB 4: Notes ---
with tab4:
    note_in = st.text_area("වැදගත් සටහන් ලියන්න")
    if st.button("Save Note"):
        conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
        c.execute('INSERT INTO system_notes (username, date, note) VALUES (?,?,?)', (st.session_state['username'], datetime.now().strftime("%Y-%m-%d %H:%M"), note_in))
        conn.commit(); conn.close(); st.success("සුරැකිණි!"); st.rerun()

# --- TAB 5: Force Statistics Report ---
with tab5:
    st.header(f"📊 දෛනික භට සංඛ්‍යා වාර්තාව - {camp_sel}")
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('police_master_system.db')
    df_f = pd.read_sql_query(f"SELECT category as 'විස්තරය', SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, row_total as 'එකතුව' FROM force_details WHERE camp = '{camp_sel}' AND date = '{today}'", conn)
    conn.close()

    if not df_f.empty:
        # Calculation
        numeric_cols = ['SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'එකතුව']
        def get_row_vals(cat):
            row = df_f[df_f['විස්තරය'] == cat]
            return row[numeric_cols].values[0] if not row.empty else [0]*len(numeric_cols)

        tot_vals = get_row_vals("මුළු භට සංඛ්‍යාව")
        duty_vals = get_row_vals("01 විශේෂ රාජකාරි පිටව ගොස් ඇති")
        off_vals = get_row_vals("02 රාජකාරි දින විවේකය පිටව ගොස් ඇති")
        
        # ඉතිරි සංඛ්‍යාව ගණනය (මුළු - (විශේෂ + විවේක))
        present_vals = [t - (d + o) for t, d, o in zip(tot_vals, duty_vals, off_vals)]
        
        # අලුත් Row එක එකතු කිරීම
        present_row = pd.DataFrame([["කදවුරේ ඉතිරි භට සංඛ්‍යාව"] + list(present_vals)], columns=['විස්තරය'] + numeric_cols)
        final_df = pd.concat([df_f, present_row], ignore_index=True)
        
        st.table(final_df)
    else:
        st.info("අද දින සඳහා දත්ත ඇතුළත් කර නැත. Tab 1 වෙත ගොස් 'භට පිරිස් දත්ත' ඇතුළත් කරන්න.")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
