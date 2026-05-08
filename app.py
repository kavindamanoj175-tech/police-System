import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import io

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Security Data Management",
    page_icon="👮",
    layout="wide"
)

# Password Hashing Function
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mandrax REAL, 
                  illegal_liquor REAL, goda REAL, sand_timber REAL, 
                  suspects INTEGER, other_records TEXT)''')
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

# --- 3. Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. Sidebar: Clock & Quick Links (සැමවිටම පෙනේ) ---
st.sidebar.title("👮 STF DBMS - v2.0")

# ශ්‍රී ලංකාවේ වේලාව (UTC + 5:30)
sl_time = datetime.now() + timedelta(hours=5, minutes=30)
st.sidebar.markdown(f"📅 **දිනය:** {sl_time.strftime('%Y-%m-%d')}")
st.sidebar.markdown(f"⏰ **වේලාව:** {sl_time.strftime('%H:%M:%S')}")
st.sidebar.divider()

# Quick Links
st.sidebar.subheader("🌐 ඉක්මන් පිවිසුම්")
st.sidebar.link_button("💬 WhatsApp Web", "https://web.whatsapp.com/")
st.sidebar.link_button("📺 YouTube", "https://www.youtube.com/")
st.sidebar.link_button("🔍 Google Search", "https://www.google.com")
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
                st.session_state['username'] = u
                st.rerun()
            else:
                st.sidebar.error("පරිශීලක නාමය හෝ මුරපදය වැරදියි!")
    else:
        new_user = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type='password')
        admin_key = st.sidebar.text_input("Admin Key (Account Creation)", type='password')
        if st.sidebar.button("ගිණුම සාදන්න"):
            if admin_key == "Police@123":
                with sqlite3.connect('police_master_system.db') as conn:
                    conn.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (new_user, make_hashes(new_password)))
                st.sidebar.success("ගිණුම සාර්ථකයි! දැන් Login තෝරන්න.")
            else:
                st.sidebar.error("Admin Key එක වැරදියි!")
    
    st.info("පද්ධතිය භාවිතා කිරීමට කරුණාකර ඇතුල් වන්න.")
    st.stop() # Login වෙනකම් ඇප් එකේ ඉතිරි කොටස පෙන්වන්නේ නැත

# --- 6. Login වූ පසු පෙන්වන දත්ත (Hierarchy & Content) ---

# සම්පූර්ණ Hierarchy එක (සියලුම කඳවුරු සමඟ)
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

admin_access = st.sidebar.text_input("Edit/Delete Admin Key", type="password")
is_admin = (admin_access == "Police@123")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# Main Interface Tabs
tabs_list = ["📝 වැටලීම් ඇතුළත් කිරීම", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා හා සෙවීම්", "📊 විශ්ලේෂණය"]
current_tab = st.radio("ප්‍රධාන මෙනුව", tabs_list, horizontal=True)

def get_db(): return sqlite3.connect('police_master_system.db')

# --- TAB 1: RAID ENTRY ---
if current_tab == "📝 වැටලීම් ඇතුළත් කිරීම":
    st.subheader(f"වැටලීම් වාර්තා ඇතුළත් කිරීම - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0)
        kg = c2.number_input("කේරළ ගංජා (කිග්‍රෑ)", 0.0)
        hr = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0)
        mx = c4.number_input("මද්‍රාස් (ග්‍රෑම්)", 0.0)
        liq = c1.number_input("මත්පැන් (ml)", 0.0)
        gd = c2.number_input("ගෝඩා (L)", 0.0)
        stmb = c3.number_input("වැලි/දැව වැටලීම්", 0.0)
        sus = c4.number_input("සැකකරුවන් ගණන", 0)
        info = st.text_area("වෙනත් විශේෂ සටහන්")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            with get_db() as conn:
                conn.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mandrax, illegal_liquor, goda, sand_timber, suspects, other_records) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (sl_time.strftime("%Y-%m-%d"), sl_time.strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, kg, hr, mx, liq, gd, stmb, sus, info))
                conn.commit()
            st.success("දත්ත සාර්ථකව පද්ධතියට එක් කරන ලදී!")

# --- TAB 2: FORCE DETAILS ---
elif current_tab == "📉 භට පිරිස් දත්ත":
    st.subheader(f"භට පිරිස් දත්ත යාවත්කාලීන කිරීම - {sub_camp}")
    with st.form("force_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "විශේෂ රාජකාරි", "නිවාඩු/විවේක"])
        total = ssp+sp+asp+ci+ip+si+ps+pc
        
        if st.form_submit_button("යාවත්කාලීන කරන්න"):
            with get_db() as conn:
                conn.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (sl_time.strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, total))
                conn.commit()
            st.success("භට පිරිස් දත්ත සාර්ථකව ගබඩා විය!")

# --- TAB 3: REPORTS & SEARCH ---
elif current_tab == "🔍 වාර්තා හා සෙවීම්":
    st.subheader("🔍 දත්ත වාර්තා සහ සෙවීම්")
    col1, col2 = st.columns(2)
    s_date = col1.date_input("සිට", sl_time)
    e_date = col2.date_input("දක්වා", sl_time)
    
    conn = get_db()
    # Safe Query with parameters
    df = pd.read_sql_query("SELECT * FROM detailed_raids WHERE zone=? AND date BETWEEN ? AND ?", 
                           conn, params=(zone_sel, s_date.strftime("%Y-%m-%d"), e_date.strftime("%Y-%m-%d")))
    
    if not df.empty:
        # Excel Export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Raids')
        st.download_button(label="📥 Excel වාර්තාව බාගත කරන්න", data=buffer.getvalue(), file_name=f"STF_Report_{zone_sel}.xlsx", mime="application/vnd.ms-excel")
        
        if is_admin:
            st.info("ඔබට දත්ත සංස්කරණය කළ හැක. වෙනස් කිරීමෙන් පසු Save කරන්න.")
            edited_df = st.data_editor(df, num_rows="dynamic")
            if st.button("Save Changes"):
                edited_df.to_sql('detailed_raids', conn, if_exists='replace', index=False)
                st.success("දත්ත යාවත්කාලීන විය!")
        else:
            st.dataframe(df)
    else:
        st.warning("තෝරාගත් කාල සීමාව සඳහා දත්ත නොමැත.")
    conn.close()

# --- TAB 4: ANALYTICS ---
elif current_tab == "📊 විශ්ලේෂණය":
    st.subheader(f"📊 {zone_sel} වැටලීම් විශ්ලේෂණය")
    conn = get_db()
    df_ana = pd.read_sql_query("SELECT * FROM detailed_raids WHERE zone=?", conn, params=(zone_sel,))
    if not df_ana.empty:
        # Bar chart for drugs
        drug_data = df_ana[['ice', 'kerala_ganja', 'heroin', 'mandrax']].sum()
        st.bar_chart(drug_data)
        
        st.divider()
        st.subheader("භට පිරිස් සාරාංශය")
        df_f = pd.read_sql_query("SELECT * FROM force_details WHERE zone=?", conn, params=(zone_sel,))
        if not df_f.empty:
            summary = df_f.groupby('category').sum(numeric_only=True).reset_index()
            st.table(summary[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PC', 'row_total']])
    else:
        st.info("විශ්ලේෂණය කිරීමට දත්ත ප්‍රමාණවත් නොමැත.")
    conn.close()
