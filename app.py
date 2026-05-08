import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import io

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(page_title="STF - Security Data Management", page_icon="👮", layout="wide")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mandrax REAL, illegal_liquor REAL, goda REAL,
                  sand_timber REAL, suspects INTEGER, other_records TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)''')
    conn.commit()
    conn.close()

def login_user(username, password):
    with sqlite3.connect('police_master_system.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (username, password))
        return c.fetchall()

init_db()

# --- 3. Sidebar & Auth ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'nav_selection' not in st.session_state: st.session_state['nav_selection'] = "📝 වැටලීම් ඇතුළත් කිරීම"

st.sidebar.title("👮 STF DBMS - v2.0")

if not st.session_state['logged_in']:
    auth_mode = st.sidebar.selectbox("පද්ධතියට ඇතුල් වන්න", ["Login", "Sign Up"])
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("ඇතුල් වන්න"):
        res = login_user(u, make_hashes(p))
        if res:
            st.session_state['logged_in'] = True
            st.rerun()
    st.stop()

# --- Sidebar එකට අලුත් දේවල් එකතු කිරීම ---
st.sidebar.divider() # වෙන් කිරීමක් දාන්න

import time # මේක උඩම import කරගන්න

# --- සජීවී වේලාව ශ්‍රී ලංකාවේ වෙලාවට (Live Clock) ---
st.sidebar.divider()
st.sidebar.subheader("📅 වත්මන් වේලාව")

# වෙලාව පෙන්වන්න හිස් තැනක් (Placeholder) එකක් හදනවා
clock_placeholder = st.sidebar.empty()

# ලංකාවේ වෙලාව හදාගන්න විදිහ
from datetime import timedelta
# UTC වෙලාවට පැය 5.5 ක් එකතු කරනවා
sl_time = datetime.now() + timedelta(hours=5, minutes=30)

# Sidebar එකේ වෙලාව update කරනවා
clock_placeholder.markdown(f"""
    ### {sl_time.strftime('%Y-%m-%d')}
    ## {sl_time.strftime('%H:%M:%S')}
""")

st.sidebar.divider()

# 2. ඉක්මන් පිවිසුම් (Quick Links) - Buttons විදිහට
st.sidebar.subheader("🌐 Quick Access")

# WhatsApp link එකේ ඔයාගේ නම්බර් එක දාන්නත් පුළුවන්
if st.sidebar.button("💬 WhatsApp"):
    js = "window.open('https://web.whatsapp.com/')"
    st.components.v1.html(f"<script>{js}</script>", height=0)

if st.sidebar.button("📺 YouTube"):
    js = "window.open('https://www.youtube.com/')"
    st.components.v1.html(f"<script>{js}</script>", height=0)

if st.sidebar.button("🔍 Google Search"):
    js = "window.open('https://www.google.com')"
    st.components.v1.html(f"<script>{js}</script>", height=0)

st.sidebar.divider()

# --- 4. Hierarchy & Navigation ---
hierarchy = {
    "යාපනය කලාපය": {
        "යාපනය සේනාංකය": {
            "වි.කා.බ යාපනය කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ නෙල්ලිඅඩි කදවුර": ["ප්‍රධාන කදවුර", "වි.කා.බ කුඩත්තනේ උප කදවුර"],
            "වි.කා.බ කිලිනොච්චිය කදවුර": ["ප්‍රධාන කදවුර"],
        },
        "මන්නාරම සේනාංකය": {
            "වි.කා.බ මන්නාරම": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ ඉලුප්පුකඩවායි": ["ප්‍රධාන කදවුර"]
        }
    },
    "වව්නියාව කලාපය": {
        "වව්නියාව සේනාංකය": {
            "වි.කා.බ වව්නියාව කදවුර": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ අනුරාධපුර කදවුර": ["ප්‍රධාන කදවුර"]
        }
    }
}

zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key = st.sidebar.text_input("Admin Access Key", type="password")
is_admin = (admin_key == "Police@123")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 5. Main Tabs ---
tabs_list = ["📝 වැටලීම් ඇතුළත් කිරීම", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා හා සෙවීම්", "📊 විශ්ලේෂණය"]
current_tab = st.radio("මෙනුව", tabs_list, horizontal=True)

# ඩේටාබේස් කනෙක්ෂන් එක පහසුවෙන් පාවිච්චි කිරීමට
def get_db_connection():
    return sqlite3.connect('police_master_system.db')

# --- TAB 1: RAID ENTRY ---
if current_tab == "📝 වැටලීම් ඇතුළත් කිරීම":
    st.subheader(f"නව වැටලීම් වාර්තාව: {sub_camp}")
    with st.form("raid_form"):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0)
        kg = c2.number_input("කේරළ ගංජා (කිග්‍රෑ)", 0.0)
        hr = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0)
        mx = c4.number_input("මද්‍රාස් (ග්‍රෑම්)", 0.0)
        liq = c1.number_input("මත්පැන් (ml)", 0.0)
        gd = c2.number_input("ගෝඩා (L)", 0.0)
        stmb = c3.number_input("වැලි/දැව (වාර්තා)", 0.0)
        sus = c4.number_input("සැකකරුවන් ගණන", 0)
        info = st.text_area("විශේෂ සටහන් (අවශ්‍යයි)")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            if info == "":
                st.error("කරුණාකර විශේෂ සටහන් හෝ වැටලීම් විස්තර ඇතුළත් කරන්න!")
            else:
                with get_db_connection() as conn:
                    conn.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mandrax, illegal_liquor, goda, sand_timber, suspects, other_records) 
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                 (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, kg, hr, mx, liq, gd, stmb, sus, info))
                st.success(f"{datetime.now().strftime('%H:%M')} ට දත්ත සාර්ථකව ගබඩා කරන ලදී.")

# --- TAB 2: FORCE DETAILS ---
elif current_tab == "📉 භට පිරිස් දත්ත":
    st.subheader(f"භට පිරිස් දත්ත යාවත්කාලීන කිරීම: {sub_camp}")
    with st.form("force_form"):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "විශේෂ රාජකාරි", "නිවාඩු/විවේක"])
        
        total = ssp+sp+asp+ci+ip+si+ps+pc
        st.info(f"වත්මන් මුළු එකතුව: {total}")
        
        if st.form_submit_button("දත්ත යාවත්කාලීන කරන්න"):
            with get_db_connection() as conn:
                conn.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, total))
            st.success("භට පිරිස් දත්ත සාර්ථකව යාවත්කාලීන විය.")

# --- TAB 3: REPORTS & EXCEL ---
elif current_tab == "🔍 වාර්තා හා සෙවීම්":
    st.subheader("🔍 දත්ත කළමනාකරණය සහ වාර්තා ලබාගැනීම")
    
    col_f1, col_f2 = st.columns(2)
    start_dt = col_f1.date_input("සිට", datetime.now())
    end_dt = col_f2.date_input("දක්වා", datetime.now())
    
    conn = get_db_connection()
    query = "SELECT * FROM detailed_raids WHERE zone=? AND date BETWEEN ? AND ?"
    df = pd.read_sql_query(query, conn, params=(zone_sel, start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")))
    
    if not df.empty:
        # Excel Download Button
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Raids')
        
        st.download_button(label="📥 Excel වාර්තාව බාගත කරගන්න", data=buffer, file_name=f"STF_Report_{zone_sel}.xlsx", mime="application/vnd.ms-excel")
        
        if is_admin:
            edited_df = st.data_editor(df, num_rows="dynamic")
            if st.button("වෙනස්කම් සුරකින්න (Save Changes)"):
                edited_df.to_sql('detailed_raids', conn, if_exists='replace', index=False)
                st.success("දත්ත යාවත්කාලීන විය!")
        else:
            st.dataframe(df)
    else:
        st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත සොයාගත නොහැක.")
    conn.close()

# --- TAB 4: ANALYTICS ---
elif current_tab == "📊 විශ්ලේෂණය":
    st.subheader(f"📊 {zone_sel} වැටලීම් විශ්ලේෂණය")
    conn = get_db_connection()
    df_ana = pd.read_sql_query("SELECT * FROM detailed_raids WHERE zone=?", conn, params=(zone_sel,))
    
    if not df_ana.empty:
        # සරල ග්‍රාෆ් එකක් - මත්ද්‍රව්‍ය වර්ග අනුව
        chart_data = df_ana[['ice', 'kerala_ganja', 'heroin', 'mandrax']].sum()
        st.bar_chart(chart_data)
        
        st.divider()
        st.subheader("භට පිරිස් සාරාංශය")
        df_f = pd.read_sql_query("SELECT * FROM force_details WHERE zone=?", conn, params=(zone_sel,))
        if not df_f.empty:
            summary = df_f.groupby('category').sum(numeric_only=True).reset_index()
            st.table(summary[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PC', 'row_total']])
    else:
        st.info("විශ්ලේෂණය කිරීමට ප්‍රමාණවත් දත්ත නොමැත.")
    conn.close()
