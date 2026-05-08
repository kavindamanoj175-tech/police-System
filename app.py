import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import io
import plotly.express as px  # අලුතින් එකතු කළා (Charts සඳහා)
from fpdf import FPDF       # අලුතින් එකතු කළා (PDF සඳහා)
import requests             # අලුතින් එකතු කළා (Alerts සඳහා)

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(page_title="STF - Security Data Management", page_icon="👮", layout="wide")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- අලුතින් එකතු කළ උපකාරක Function (PDF සෑදීම) ---
def generate_pdf(df, title):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt=f"STF REPORT: {title}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Header
    pdf.set_font("Arial", 'B', 8)
    cols = df.columns.tolist()[:8] # ඉඩ මදි නිසා වැදගත්ම columns 8 ක් පමණක් ගනිමු
    for col in cols:
        pdf.cell(23, 10, str(col), border=1)
    pdf.ln()
    
    # Rows
    pdf.set_font("Arial", size=8)
    for index, row in df.iterrows():
        for col in cols:
            pdf.cell(23, 10, str(row[col]), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- අලුතින් එකතු කළ උපකාරක Function (WhatsApp/SMS Alert) ---
def send_admin_alert(user_name):
    # මචන් මෙතනට ඔයාගේ Phone Number එක සහ CallMeBot API Key එක දාන්න
    # api_key = "ඔයාගේ_KEY_එක"
    # phone = "947XXXXXXXX"
    # url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text=New+User+Registration:+{user_name}&apikey={api_key}"
    # try: requests.get(url)
    # except: pass
    pass

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT PRIMARY KEY, password TEXT, role TEXT, status TEXT)')
    try:
        c.execute('ALTER TABLE userstable ADD COLUMN status TEXT DEFAULT "Approved"')
    except: pass 
    
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
                  vehicle_no TEXT, vehicle_type TEXT, status TEXT, repair_details TEXT)''')
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
    st.session_state['username'] = ""
    st.session_state['role'] = 'User'

# --- 4. Sidebar ---
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("👮 STF DBMS - v3.0 Pro")
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
                if res[3] == "Approved":
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = res[0]
                    st.session_state['role'] = res[2] 
                    st.rerun()
                else:
                    st.sidebar.warning("ඔබේ ගිණුම තවමත් අනුමත කර නැත.")
            else: st.sidebar.error("Username හෝ Password වැරදියි!")
    else:
        admin_key = st.sidebar.text_input("Admin Key (Account Creation - optional)", type='password')
        if st.sidebar.button("ගිණුම සාදන්න"):
            role = "Admin" if admin_key == "Police@123" else "User"
            status = "Approved" if admin_key == "Police@123" else "Pending"
            try:
                with sqlite3.connect('police_master_system.db') as conn:
                    conn.execute('INSERT INTO userstable(username, password, role, status) VALUES (?,?,?,?)', (u, make_hashes(p), role, status))
                    conn.commit()
                if status == "Pending":
                    st.sidebar.info("සාර්ථකයි! Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")
                    send_admin_alert(u) # Admin හට alert එකක් යවයි
                else:
                    st.sidebar.success(f"{u} ({role}) සාර්ථකයි!")
            except sqlite3.IntegrityError:
                st.sidebar.error("මේ පරිශීලක නාමය දැනටමත් ඇත.")
            except: st.sidebar.error("ගැටලුවක්!")
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

# --- RAID TAB ---
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
                conn.commit()
            st.success("දත්ත සාර්ථකව සුරැකිණි!")

# --- FORCE TAB ---
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
                conn.commit()
            st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")

# --- VEHICLE TAB ---
elif current_tab == "🚔 වාහන":
    st.subheader(f"වාහන පාලනය - {sub_camp}")
    v_tab1, v_tab2 = st.tabs(["➕ ඇතුළත් කිරීම", "📋 ලේඛනය"])
    with v_tab1:
        with st.form("v_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            v_no = col1.text_input("වාහන අංකය")
            v_type = col1.selectbox("වාර්ගය", ["Land Rover", "Jeep", "Cab", "Truck", "Motorbike", "Bowser", "Trackter",  "Land Master"])
            v_status = col2.selectbox("තත්ත්වය", ["ධාවනය කළ හැක", "අලුත්වැඩියාවට යවා ඇත", "ධාවනය කළ නොහැක"])
            v_info = col2.text_area("විස්තර")
            if st.form_submit_button("සුරකින්න"):
                with get_db() as conn:
                    conn.execute('INSERT INTO vehicle_records (date, zone, division, camp, vehicle_no, vehicle_type, status, repair_details) VALUES (?,?,?,?,?,?,?,?)',
                                 (sl_time.strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, v_no, v_type, v_status, v_info))
                    conn.commit()
                st.success("වාහන දත්ත සුරැකිණි!")
    with v_tab2:
        conn = get_db()
        st.dataframe(pd.read_sql_query("SELECT * FROM vehicle_records WHERE zone=?", conn, params=(zone_sel,)), use_container_width=True)
        conn.close()

# --- REPORT TAB (PDF සහ Excel එකතු කළා) ---
elif current_tab == "🔍 වාර්තා":
    st.subheader("🔍 දත්ත වාර්තා සහ පරිශීලක පාලනය")
    
    if st.session_state['role'] == "Admin":
        admin_tab1, admin_tab2 = st.tabs(["📊 දත්ත වාර්තා", "👤 පරිශීලක අනුමැතිය"])
        
        with admin_tab1:
            rep_type = st.selectbox("දත්ත වර්ගය තෝරන්න", ["detailed_raids", "force_details", "vehicle_records"])
            conn = get_db()
            df = pd.read_sql_query(f"SELECT * FROM {rep_type} WHERE zone=?", conn, params=(zone_sel,))
            
            # Download Section
            col_ex, col_pdf = st.columns(2)
            # Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            col_ex.download_button(label="📥 Excel බාගත කරන්න", data=output.getvalue(), file_name=f"{rep_type}.xlsx")
            
            # PDF
            if col_pdf.button("📄 PDF වාර්තාව සකසන්න"):
                pdf_data = generate_pdf(df, rep_type.replace('_', ' ').upper())
                st.download_button(label="📥 PDF බාගත කරන්න", data=pdf_data, file_name=f"{rep_type}.pdf", mime="application/pdf")
            
            st.divider()
            edited = st.data_editor(df, num_rows="dynamic")
            if st.button("වෙනස්කම් සුරකින්න"):
                edited.to_sql(rep_type, conn, if_exists='replace', index=False)
                st.success("දත්ත යාවත්කාලීන විය!")
            conn.close()
            
        with admin_tab2:
            st.subheader("අනුමැතිය අපේක්ෂිත නව ගිණුම්")
            conn = get_db()
            pending_users = pd.read_sql_query("SELECT username, role, status FROM userstable WHERE status='Pending'", conn)
            if not pending_users.empty:
                for index, row in pending_users.iterrows():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.write(f"**{row['username']}** ({row['role']})")
                    if col2.button("Approve", key=f"app_{row['username']}"):
                        conn.execute("UPDATE userstable SET status='Approved' WHERE username=?", (row['username'],))
                        conn.commit(); st.rerun()
                    if col3.button("Reject", key=f"del_{row['username']}"):
                        conn.execute("DELETE FROM userstable WHERE username=?", (row['username'],))
                        conn.commit(); st.rerun()
            else: st.info("අලුත් ගිණුම් නැත.")
            conn.close()
    else:
        rep_type = st.selectbox("වර්ගය", ["detailed_raids", "force_details", "vehicle_records"])
        conn = get_db()
        st.dataframe(pd.read_sql_query(f"SELECT * FROM {rep_type} WHERE zone=?", conn, params=(zone_sel,)), use_container_width=True)
        conn.close()

# --- ANALYSIS TAB (Charts එකතු කළා) ---
elif current_tab == "📊 විශ්ලේෂණය":
    st.subheader("📊 තත්‍ය කාලීන දත්ත විශ්ලේෂණය")
    conn = get_db()
    df_raids = pd.read_sql_query("SELECT * FROM detailed_raids", conn)
    
    if not df_raids.empty:
        c1, c2 = st.columns(2)
        
        # Chart 1: මත්ද්‍රව්‍ය වැටලීම් සාරාංශය (Bar Chart)
        drug_data = df_raids[['ice', 'kerala_ganja', 'heroin', 'mandrax']].sum().reset_index()
        drug_data.columns = ['වර්ගය', 'මුළු ප්‍රමාණය (ග්‍රෑම්/කිග්‍රෑ)']
        fig1 = px.bar(drug_data, x='වර්ගය', y='මුළු ප්‍රමාණය (ග්‍රෑම්/කිග්‍රෑ)', color='වර්ගය', title="මත්ද්‍රව්‍ය වැටලීම් සාරාංශය")
        c1.plotly_chart(fig1, use_container_width=True)
        
        # Chart 2: සැකකරුවන් ප්‍රමාණය (Pie Chart)
        fig2 = px.pie(df_raids, values='suspects', names='camp', title="කදවුරු අනුව සැකකරුවන් අත්අඩංගුවට ගැනීම")
        c2.plotly_chart(fig2, use_container_width=True)
        
        # Chart 3: කාලය අනුව වැටලීම් (Line Chart)
        fig3 = px.line(df_raids, x='date', y='ice', title="දින අනුව අයිස් (ICE) වැටලීම් ප්‍රවණතාවය")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("පෙන්වීමට දත්ත ප්‍රමාණවත් නැත.")
    conn.close()
