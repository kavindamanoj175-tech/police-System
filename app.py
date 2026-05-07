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

# --- 3. ධුරාවලිය ---
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
    }
}

# --- 4. Sidebar (Login & Signup) ---
st.sidebar.title("👮 STF DBMS")
try:
    img = Image.open("logo.png")
    st.sidebar.image(img, use_container_width=True)
except:
    st.sidebar.info("Logo not found.")

menu = ["Login", "SignUp"]
choice = st.sidebar.selectbox("පද්ධතියට ඇතුළු වන්න", menu)

if choice == "Login":
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        hashed_pswd = make_hashes(p)
        result = login_user(u, check_hashes(p, hashed_pswd))
        if result:
            st.session_state['logged_in'] = True
            st.session_state['username'] = u
            st.sidebar.success(f"සාදරයෙන් පිළිගනිමු {u}!")
        else:
            st.sidebar.error("අනුමත කර නැත හෝ වැරදි දත්ත!")

elif choice == "SignUp":
    new_user = st.sidebar.text_input("Username")
    new_password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Create Account"):
        add_userdata(new_user, make_hashes(new_password))
        st.sidebar.success("ගිණුම නිර්මාණය විය! කරුණාකර Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")

# Admin Panel Logic
st.sidebar.divider()
admin_key = st.sidebar.text_input("Admin Key (Security)", type="password")
is_admin = (admin_key == "Police@123")

if is_admin:
    st.sidebar.warning("Admin Access: ON")
    pending = get_pending_users()
    if pending:
        u_to_app = st.sidebar.selectbox("අනුමත කිරීමට යූසර් තෝරන්න", [u[0] for u in pending])
        if st.sidebar.button("Confirm Approval"):
            approve_user(u_to_app); st.sidebar.success(f"{u_to_app} අනුමත කරන ලදී!"); st.rerun()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.info("කරුණාකර පද්ධතියට ලොග් වන්න.")
    st.stop()

# --- 5. Main System ---
st.title("🚨 Special Task Force - Data Management System")

zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
camps_list = []
for main_camp, sub_camps in hierarchy[zone_sel][div_sel].items():
    camps_list.append(main_camp); camps_list.extend(sub_camps)
camp_sel = st.sidebar.selectbox("කදවුර / උප කදවුර", camps_list)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "🔍 වැටලීම් වාර්තා", "📊 සාරාංශ ගත වාර්තා", "📝 සටහන් පොත", "📉 භට පිරිස් වාර්තාව"])

# --- TAB 1: Data Entry ---
with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🕵️ වැටලීම් දත්ත")
        with st.form("raid_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
            k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", 0.0)
            heroin = c1.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
            suspects = c2.number_input("සැකකරුවන්", 0)
            other = st.text_area("වෙනත්")
            if st.form_submit_button("වැටලීම සුරකින්න"):
                now = datetime.now()
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, suspects, other_records) 
                             VALUES (?,?,?,?,?,?,?,?,?,?)''', 
                          (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), zone_sel, div_sel, camp_sel, ice, k_ganja, heroin, suspects, other))
                conn.commit(); conn.close(); st.success("දත්ත ගබඩා විය!")

    with col_b:
        st.subheader("👮 භට පිරිස් දත්ත")
        with st.form("force_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            ssp, sp, asp = f1.number_input("SSP", 0), f2.number_input("SP", 0), f3.number_input("ASP", 0)
            ci, ip, si = f1.number_input("CI", 0), f2.number_input("IP", 0), f3.number_input("SI", 0)
            ps, psd, pc = f1.number_input("PS", 0), f2.number_input("PSD", 0), f3.number_input("PC", 0)
            pcd = f1.number_input("PCD", 0)
            cat = st.selectbox("කාණ්ඩය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි පිටව ගොස් ඇති", "02 රාජකාරි දින විවේකය පිටව ගොස් ඇති"])
            if st.form_submit_button("භට දත්ත සුරකින්න"):
                tot = ssp+sp+asp+ci+ip+si+ps+psd+pc+pcd
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, row_total) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, camp_sel, cat, ssp, sp, asp, ci, ip, si, ps, psd, pc, pcd, tot))
                conn.commit(); conn.close(); st.success("භට දත්ත සුරැකිණි!")

# --- TAB 2: Raid Filtering & Admin Edit/Delete ---
with tab2:
    st.header("🔍 වැටලීම් කළමනාකරණය")
    f1, f2 = st.columns(2)
    s_dt, e_dt = f1.date_input("ආරම්භය", datetime.now()), f2.date_input("අවසානය", datetime.now())
    conn = sqlite3.connect('police_master_system.db')
    df_r = pd.read_sql_query(f"SELECT * FROM detailed_raids WHERE date BETWEEN '{s_dt}' AND '{e_dt}' AND camp='{camp_sel}'", conn)
    
    if not df_r.empty:
        if is_admin:
            st.info("💡 Admin Mode: Edit කර Update ඔබන්න.")
            edited_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("Raid Database Update"):
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM detailed_raids WHERE id IN ({','.join(map(str, df_r['id'].tolist()))})")
                edited_r.to_sql('detailed_raids', conn, if_exists='append', index=False)
                conn.commit(); st.success("යාවත්කාලීන විය!"); st.rerun()
        else:
            st.dataframe(df_r, use_container_width=True, hide_index=True)
    conn.close()

# Other Tabs...
with tab3:
    st.write("📈 පද්ධති විශ්ලේෂණය...")
with tab4:
    st.write("📝 සටහන් පොත...")
# --- TAB 5: Force Report & Admin Edit/Delete ---
with tab5:
    st.header(f"📊 භට සංඛ්‍යා වාර්තාව - {camp_sel}")
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect('police_master_system.db')
    df_f = pd.read_sql_query(f"SELECT * FROM force_details WHERE camp = '{camp_sel}' AND date = '{today}'", conn)

    if not df_f.empty:
        # Display Summary
        numeric_cols = ['SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'row_total']
        def get_vals(cat):
            row = df_f[df_f['category'] == cat]
            return row[numeric_cols].values[0] if not row.empty else [0]*len(numeric_cols)

        t_v, d_v, o_v = get_vals("මුළු භට සංඛ්‍යාව"), get_vals("01 විශේෂ රාජකාරි පිටව ගොස් ඇති"), get_vals("02 රාජකාරි දින විවේකය පිටව ගොස් ඇති")
        p_v = [t - (d + o) for t, d, o in zip(t_v, d_v, o_v)]
        
        summary = df_f[['category'] + numeric_cols].copy()
        res_row = pd.DataFrame([["කදවුරේ ඉතිරි භට සංඛ්‍යාව"] + list(p_v)], columns=['category'] + numeric_cols)
        st.table(pd.concat([summary, res_row], ignore_index=True))

        if is_admin:
            st.divider()
            st.subheader("⚙️ Admin: භට පිරිස් දත්ත සංස්කරණය")
            edited_f = st.data_editor(df_f, num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("Force Database Update"):
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM force_details WHERE id IN ({','.join(map(str, df_f['id'].tolist()))})")
                edited_f.to_sql('force_details', conn, if_exists='append', index=False)
                conn.commit(); st.success("භට දත්ත යාවත්කාලීන විය!"); st.rerun()
    else:
        st.info("අද දිනට දත්ත නැත.")
    conn.close()
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
