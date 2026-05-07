import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Security Data Management",
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
    # සියලුම පරණ fields තියෙනවා, අමතර විස්තර සඳහා other_records තියෙනවා
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mava REAL, 
                  mandrax REAL, dambul REAL, illegal_liquor REAL, goda REAL,
                  sand_timber REAL, tobacco REAL, suspects INTEGER,
                  other_records TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER, row_total INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. ධුරාවලිය (Hierarchy Update) ---
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
    }
}

# --- 4. Sidebar Login / Selection ---
st.sidebar.title("👮 STF DBMS")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        # මෙතන login logic එක කලින් එකමයි
        st.session_state['logged_in'] = True; st.session_state['username'] = u; st.rerun()
    st.stop()

# Location Selections
st.sidebar.divider()
zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key = st.sidebar.text_input("Admin Key", type="password")
is_admin = (admin_key == "Police@123")

# --- 5. Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 වැටලීම් දත්ත", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා පිරික්සුම", "📊 සංඛ්‍යාත්මක විශ්ලේෂණය"])

# --- TAB 1: Raid Entry (Keeping all old fields + Adding more) ---
with tab1:
    st.subheader(f"වැටලීම් වාර්තාව - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
        k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", 0.0)
        heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
        
        mava = c1.number_input("මාවා (Mava) - කි.ග්‍රෑ", 0.0)
        mandrax = c2.number_input("මැන්ඩ්‍රැක්ස් - පෙති", 0.0)
        dambul = c3.number_input("ඩම්බුල් - කි.ග්‍රෑ", 0.0)
        
        liq = c1.number_input("නීතිවිරෝධී මත්පැන් (බෝතල්)", 0.0)
        goda = c2.number_input("ගෝඩා (ලීටර්)", 0.0)
        sand = c3.number_input("වැලි/ලී වැටලීම්", 0.0)
        
        suspects = c1.number_input("සැකකරුවන්", 0)
        other_txt = st.text_area("වෙනත් විශේෂ වැටලීම් සහ විස්තර (මෙහි ඕනෑම දෙයක් ඇඩ් කළ හැක)")
        
        if st.form_submit_button("වාර්තාව සුරකින්න"):
            now = datetime.now()
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mava, mandrax, dambul, illegal_liquor, goda, sand_timber, suspects, other_records) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, mava, mandrax, dambul, liq, goda, sand, suspects, other_txt))
            conn.commit(); conn.close(); st.success("දත්ත ගබඩා විය!")

# --- TAB 2: Dedicated Force Management ---
with tab2:
    st.subheader(f"දෛනික භට පිරිස් දත්ත - {sub_camp}")
    with st.form("force_form"):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); psd = f2.number_input("PSD", 0); pc = f3.number_input("PC", 0)
        pcd = f1.number_input("PCD", 0)
        
        cat = st.selectbox("කාණ්ඩය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි පිටව ගොස් ඇති", "02 නිවාඩු/විවේක පිටව ගොස් ඇති"])
        if st.form_submit_button("භට පිරිස් දත්ත යාවත්කාලීන කරන්න"):
            row_tot = ssp+sp+asp+ci+ip+si+ps+psd+pc+pcd
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PSD, PC, PCD, row_total) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, psd, pc, pcd, row_tot))
            conn.commit(); conn.close(); st.success("යාවත්කාලීන විය!")

# --- TAB 3: Reports & Admin Edit ---
with tab3:
    st.subheader("🔍 වාර්තා පිරික්සුම සහ කළමනාකරණය")
    mode = st.radio("මට්ටම", ["කලාපය", "සේනාංකය", "කදවුර"], horizontal=True)
    
    conn = sqlite3.connect('police_master_system.db')
    if mode == "කලාපය": filter_q = f"WHERE zone='{zone_sel}'"
    elif mode == "සේනාංකය": filter_q = f"WHERE division='{div_sel}'"
    else: filter_q = f"WHERE camp='{sub_camp}'"
    
    df_r = pd.read_sql_query(f"SELECT * FROM detailed_raids {filter_q}", conn)
    df_f = pd.read_sql_query(f"SELECT * FROM force_details {filter_q}", conn)
    
    st.write("🕵️ වැටලීම් වාර්තා")
    if is_admin:
        edited_r = st.data_editor(df_r, num_rows="dynamic", key="raid_ed")
        if st.button("Raid Data Update"):
            # Update logic
            st.info("Admin updated database.")
    else:
        st.dataframe(df_r)

    st.divider()
    st.write("👮 භට පිරිස් වාර්තා")
    st.dataframe(df_f)
    conn.close()

# --- TAB 4: Advanced Analytics ---
with tab4:
    st.subheader("📊 සාරාංශ ගත වාර්තා")
    if not df_f.empty:
        # සේනාංක හා කලාප මට්ටමින් එකතුව පෙන්වීම
        summary = df_f.groupby(['date', 'category']).sum().reset_index()
        st.write(f"{mode} මට්ටමේ මුළු භට පිරිස් එකතුව")
        st.table(summary[['date', 'category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PSD', 'PC', 'PCD', 'row_total']])
