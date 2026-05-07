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
    # පරිශීලක වගුව
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT, is_approved INTEGER DEFAULT 0)')
    
    # විස්තරාත්මක වැටලීම් වගුව (Screenshot එකේ අයිතම සියල්ල සහිතව)
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mava REAL, 
                  mandrax REAL, dambul REAL, illegal_liquor REAL, goda REAL,
                  unidentified_liquor REAL, gov_liquor REAL, sand_timber REAL,
                  tobacco REAL, cigarettes REAL, fireworks REAL, suspects INTEGER,
                  other_records TEXT)''')
    
    # භට පිරිස්, අපරාධකරුවන් සහ සටහන් වගු
    c.execute('''CREATE TABLE IF NOT EXISTS force_stats (date TEXT, zone TEXT, division TEXT, camp TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, note TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, file_name TEXT, file_data BLOB)''')
    
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('INSERT INTO userstable(username,password,is_approved) VALUES (?,?,0)', (username, password))
    conn.commit(); conn.close()

def login_user(username, password):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password =? AND is_approved = 1', (username, password))
    return c.fetchall()

def get_pending_users():
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('SELECT username FROM userstable WHERE is_approved = 0')
    return c.fetchall()

def approve_user(username):
    conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
    c.execute('UPDATE userstable SET is_approved = 1 WHERE username = ?', (username,))
    conn.commit(); conn.close()

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
    st.sidebar.info("Logo not found. Upload 'logo.png' to GitHub.")

# Admin Panel
st.sidebar.divider()
admin_key = st.sidebar.text_input("Admin Key", type="password")
if admin_key == "Police@123":
    pending = get_pending_users()
    if pending:
        u_to_app = st.sidebar.selectbox("Approve User", [u[0] for u in pending])
        if st.sidebar.button("Confirm Approval"):
            approve_user(u_to_app); st.sidebar.success("Approved!"); st.rerun()

# Login Logic
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    auth_choice = st.sidebar.radio("Login Options", ["Login", "Sign Up"])
    if auth_choice == "Login":
        u = st.sidebar.text_input("User Name")
        p = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            if login_user(u, check_hashes(p, make_hashes(p))):
                st.session_state['logged_in'] = True; st.session_state['username'] = u; st.rerun()
            else: st.sidebar.error("අනුමත කර නැත හෝ වැරදි දත්ත!")
    else:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type='password')
        if st.button("Register"):
            add_userdata(new_u, make_hashes(new_p)); st.info("ලියාපදිංචි විය. Admin අනුමැතිය බලාපොරොත්තු වන්න.")

# --- 5. Main System ---
if st.session_state['logged_in']:
    st.title("🚨 Special Task Force - Data Management System")
    
    # Global Selections
    zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
    div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
    camp_sel = st.sidebar.selectbox("කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 දත්ත ඇතුළත් කිරීම", "🔍 විස්තරාත්මක වාර්තා (Filtering)", "📊 සාරාංශ ගත වාර්තා", "📝 සටහන් පොත"])

    # --- TAB 1: Data Entry ---
    with tab1:
        st.header(f"🕵️ වැටලීම් දත්ත ඇතුළත් කිරීම - {camp_sel}")
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
            other_text = st.text_area("වෙනත් විස්තර (ආයුධ/වාහන අංක ආදිය)")
            
            if st.form_submit_button("වාර්තාව සුරකින්න"):
                now = datetime.now()
                conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
                c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mava, mandrax, dambul, illegal_liquor, goda, sand_timber, suspects, other_records) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), zone_sel, div_sel, camp_sel, ice, k_ganja, heroin, mava, mandrax, dambul, liq_ill, goda, sand_timber, suspects, other_text))
                conn.commit(); conn.close(); st.success("දත්ත සාර්ථකව ගබඩා විය!")

    # --- TAB 2: Detailed Filtering ---
    with tab2:
        st.header("🔍 මට්ටම් අනුව වාර්තා පෙරීම")
        filter_level = st.radio("වාර්තා පෙන්විය යුතු මට්ටම", ["කලාප මට්ටමින්", "සේනාංක මට්ටමින්", "කදවුරු මට්ටමින්"], horizontal=True)
        
        f1, f2 = st.columns(2)
        start_dt = f1.date_input("ආරම්භක දිනය")
        end_dt = f2.date_input("අවසාන දිනය")
        
        conn = sqlite3.connect('police_master_system.db')
        query = f"SELECT * FROM detailed_raids WHERE date BETWEEN '{start_dt}' AND '{end_dt}'"
        
        if filter_level == "කලාප මට්ටමින්":
            query += f" AND zone = '{zone_sel}'"
        elif filter_level == "සේනාංක මට්ටමින්":
            query += f" AND division = '{div_sel}'"
        else:
            query += f" AND camp = '{camp_sel}'"
            
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Excel Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='RaidReport')
            st.download_button(label="📥 Excel වාර්තාව බාගත කරන්න", data=output.getvalue(), file_name=f"STF_Report_{filter_level}.xlsx")
        else:
            st.info("තෝරාගත් කාල සීමාව සහ මට්ටම සඳහා දත්ත සොයාගත නොහැක.")

    # --- TAB 3: Visual Analysis ---
    with tab3:
        st.header("📈 විශ්ලේෂණ සාරාංශය")
        conn = sqlite3.connect('police_master_system.db')
        df_all = pd.read_sql_query("SELECT * FROM detailed_raids", conn)
        conn.close()
        
        if not df_all.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("කලාපීය මට්ටමින් සැකකරුවන්")
                fig1 = px.bar(df_all, x="zone", y="suspects", color="division", barmode="group")
                st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                st.subheader("සේනාංක අනුව වැටලීම් ව්‍යාප්තිය")
                fig2 = px.pie(df_all, names="division", values="suspects", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("විශ්ලේෂණය කිරීමට ප්‍රමාණවත් දත්ත නැත.")

    # --- TAB 4: Notes ---
    with tab4:
        st.subheader("📝 පද්ධති සටහන් (Log)")
        note_in = st.text_area("වැදගත් සටහන් මෙතන ලියන්න")
        if st.button("Save Note"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('INSERT INTO system_notes (username, date, note) VALUES (?,?,?)', (st.session_state['username'], datetime.now().strftime("%Y-%m-%d %H:%M"), note_in))
            conn.commit(); conn.close(); st.rerun()
            
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False; st.rerun()
