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
    
    # Force Stats Table එක සැකසීම
    c.execute('''CREATE TABLE IF NOT EXISTS force_stats 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT, 
                  SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER, total INTEGER)''')
    
    # වැදගත්: පරණ Database එකක 'total' column එක නැත්නම් ඒක එකතු කිරීම
    try:
        c.execute("ALTER TABLE force_stats ADD COLUMN total INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # දැනටමත් තිබේ නම් දෝෂය නොසලකා හරින්න

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
camp_sel = st.sidebar.selectbox("කදවුර", list(hierarchy[zone_sel][div_sel].keys()))

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "🔍 වැටලීම් වාර්තා", "📊 විශ්ලේෂණය", "📝 සටහන් පොත", "📉 භට පිරිස් වාර්තාව"])

with tab1:
    col_raid, col_force = st.columns(2)
    with col_raid:
        st.subheader("🕵️ වැටලීම් දත්ත")
        with st.form("raid_form", clear_on_submit=True):
            ice = st.number_input("අයිස් (ICE) - ග්‍රෑම්", min_value=0.0)
            k_ganja = st.number_input("කේරළ ගංජා - කි.ග්‍රෑ", min_value=0.0)
            heroin = st.number_input("හෙරොයින් - ග්‍රෑම්", min_value=0.0)
            suspects = st.number_input("සැකකරුවන්", min_value=0)
            other = st.text_area("වෙනත්")
            if st.form_submit_button("වැටලීම සුරකින්න"):
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, suspects, other_records) VALUES (?,?,?,?,?,?,?,?,?,?)',
                          (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, camp_sel, ice, k_ganja, heroin, suspects, other))
                conn.commit(); conn.close(); st.success("දත්ත සුරැකිණි!")

    with col_force:
        st.subheader("👮 භට පිරිස් දත්ත")
        with st.form("force_form", clear_on_submit=True):
            ssp = st.number_input("SSP", min_value=0)
            sp = st.number_input("SP", min_value=0)
            asp = st.number_input("ASP", min_value=0)
            ci = st.number_input("CI", min_value=0)
            ip = st.number_input("IP", min_value=0)
            si = st.number_input("SI", min_value=0)
            ps = st.number_input("PS", min_value=0)
            psd = st.number_input("PS (Drive)", min_value=0)
            pc = st.number_input("PC", min_value=0)
            pcd = st.number_input("PC (Drive)", min_value=0)
            if st.form_submit_button("භට පිරිස් සුරකින්න"):
                total_f = ssp+sp+asp+ci+ip+si+ps+psd+pc+pcd
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('INSERT INTO force_stats (date, zone, division, camp, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, total) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, camp_sel, ssp, sp, asp, ci, ip, si, ps, psd, pc, pcd, total_f))
                conn.commit(); conn.close(); st.success("භට පිරිස් දත්ත සුරැකිණි!")

with tab2:
    st.header("🔍 වැටලීම් කළමනාකරණය")
    start_dt = st.date_input("ආරම්භය", value=datetime.now(), key="r1")
    end_dt = st.date_input("අවසානය", value=datetime.now(), key="r2")
    conn = sqlite3.connect('police_master_system.db')
    df_r = pd.read_sql_query(f"SELECT * FROM detailed_raids WHERE date BETWEEN '{start_dt}' AND '{end_dt}'", conn)
    conn.close()
    if not df_r.empty:
        if is_admin:
            edited_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, key="ed_r", hide_index=True)
            if st.button("Raid Database Update"):
                conn = sqlite3.connect('police_master_system.db'); cursor = conn.cursor()
                cursor.execute(f"DELETE FROM detailed_raids WHERE id IN ({','.join(map(str, df_r['id'].tolist()))})")
                edited_r.to_sql('detailed_raids', conn, if_exists='append', index=False)
                conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
        else: st.dataframe(df_r, use_container_width=True)

with tab5:
    st.header(f"📊 දෛනික භට සංඛ්‍යා වාර්තාව")
    conn = sqlite3.connect('police_master_system.db')
    # මෙතනදී column එකක් නැති වුණොත් එන ප්‍රශ්නය විසඳා ඇත
    try:
        df_f = pd.read_sql_query(f"SELECT zone, division, camp, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, total FROM force_stats WHERE division = '{div_sel}'", conn)
        if not df_f.empty:
            df_f.columns = ['කලාපය', 'සේනාංකය', 'කදවුර', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'එකතුව']
            numeric_cols = ['SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'එකතුව']
            totals = df_f[numeric_cols].sum().to_frame().T
            totals['කලාපය'] = ''; totals['සේනාංකය'] = 'මුළු එකතුව'; totals['කදවුර'] = ''
            display_df = pd.concat([df_f, totals], ignore_index=True)
            st.table(display_df)
            
            if is_admin:
                st.divider()
                st.subheader("⚙️ දත්ත සංස්කරණය")
                df_edit_f = pd.read_sql_query(f"SELECT * FROM force_stats WHERE division = '{div_sel}'", conn)
                edited_f = st.data_editor(df_edit_f, num_rows="dynamic", use_container_width=True, key="ed_f", hide_index=True)
                if st.button("Force Database Update"):
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM force_stats WHERE id IN ({','.join(map(str, df_edit_f['id'].tolist()))})")
                    edited_f.to_sql('force_stats', conn, if_exists='append', index=False)
                    conn.commit(); st.success("Updated!"); st.rerun()
        else:
            st.info("දත්ත නැත.")
    except Exception as e:
        st.error("Database එක යාවත්කාලීන වෙමින් පවතී. කරුණාකර මද වෙලාවකින් උත්සාහ කරන්න හෝ Database එක Reset කරන්න.")
    finally:
        conn.close()

# අනෙක් Tab දෙක (විශ්ලේෂණය සහ සටහන්)
with tab3:
    conn = sqlite3.connect('police_master_system.db'); df_all = pd.read_sql_query("SELECT * FROM detailed_raids", conn); conn.close()
    if not df_all.empty: st.plotly_chart(px.bar(df_all, x="zone", y="suspects", color="division"), use_container_width=True)

with tab4:
    note_in = st.text_area("සටහන")
    if st.button("Save Note"):
        conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
        c.execute('INSERT INTO system_notes (username, date, note) VALUES (?,?,?)', (st.session_state['username'], datetime.now().strftime("%Y-%m-%d %H:%M"), note_in))
        conn.commit(); conn.close(); st.success("Saved!"); st.rerun()

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
