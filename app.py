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
    page_title="STF - Strategic Data Management",
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
                  sand_timber REAL, tobacco REAL, suspects INTEGER,
                  other_records TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER, row_total INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS system_notes (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, note TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. ධුරාවලිය (වව්නියාව ඇතුළුව සම්පූර්ණ ලැයිස්තුව) ---
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
            "වි.කා.බ වව්නියාව": ["ප්‍රධාන කදවුර", "වි.කා.බ සෙට්ටිකුලම උප කදවුර"],
            "වි.කා.බ මඩුකන්ද": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ ඊරට්ටපෙරියකුලම": ["ප්‍රධාන කදවුර"],
            "වි.කා.බ කැබිතිගොල්ලෑව": ["ප්‍රධාන කදවුර", "වි.කා.බ පදවිය උප කදවුර"]
        }
    }
}

# --- 4. Sidebar & Logo ---
st.sidebar.title("👮 STF DBMS")
try:
    # Logo එක ආයෙත් දැම්මා
    img = Image.open("logo.png")
    st.sidebar.image(img, use_container_width=True)
except:
    st.sidebar.info("Logo (logo.png) not found.")

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    menu = ["Login", "SignUp"]
    choice = st.sidebar.selectbox("Login Menu", menu)
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Access"):
        st.session_state['logged_in'] = True; st.session_state['username'] = u; st.rerun()
    st.stop()

# Location Selections
st.sidebar.divider()
zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key = st.sidebar.text_input("Admin Key (For Edit/Delete)", type="password")
is_admin = (admin_key == "Police@123")

# --- 5. Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 වැටලීම් ඇතුළත් කිරීම", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා පිරික්සුම (Edit/Delete)", "📊 විශ්ලේෂණය", "📝 සටහන්"])

# --- TAB 1: Raid Entry ---
with tab1:
    st.subheader(f"වැටලීම් වාර්තාව - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
        k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", 0.0)
        heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
        liq = c1.number_input("මත්පැන් (බෝතල්)", 0.0)
        goda = c2.number_input("ගෝඩා (ලීටර්)", 0.0)
        sand = c3.number_input("වැලි/ලී වැටලීම්", 0.0)
        suspects = c1.number_input("සැකකරුවන්", 0)
        other_txt = st.text_area("අමතර විස්තර සහ වෙනත් වැටලීම්")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, illegal_liquor, goda, sand_timber, suspects, other_records) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, liq, goda, sand, suspects, other_txt))
            conn.commit(); conn.close(); st.success("සාර්ථකව සුරැකිණි!")

# --- TAB 2: Force Entry ---
with tab2:
    st.subheader(f"භට පිරිස් දත්ත - {sub_camp}")
    with st.form("force_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි", "02 නිවාඩු/විවේක"])
        if st.form_submit_button("යාවත්කාලීන කරන්න"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, (ssp+sp+asp+ci+ip+si+ps+pc)))
            conn.commit(); conn.close(); st.success("භට පිරිස් දත්ත සුරැකිණි!")

# --- TAB 3: Edit/Delete Section (වැදගත්ම කොටස) ---
with tab3:
    st.subheader("🔍 දත්ත කළමනාකරණය (Edit/Delete)")
    conn = sqlite3.connect('police_master_system.db')
    
    # වැටලීම් දත්ත සංස්කරණය
    st.write("---")
    st.write("### 🕵️ වැටලීම් වාර්තා")
    df_r = pd.read_sql_query(f"SELECT * FROM detailed_raids WHERE zone='{zone_sel}'", conn)
    if is_admin:
        edited_r = st.data_editor(df_r, num_rows="dynamic", key="raid_edit_table")
        if st.button("වැටලීම් දත්ත Update කරන්න"):
            df_r.to_sql('detailed_raids', conn, if_exists='replace', index=False)
            st.success("වැටලීම් දත්ත යාවත්කාලීන විය!")
    else:
        st.dataframe(df_r)

    # භට පිරිස් දත්ත සංස්කරණය
    st.write("---")
    st.write("### 👮 භට පිරිස් වාර්තා")
    df_f = pd.read_sql_query(f"SELECT * FROM force_details WHERE zone='{zone_sel}'", conn)
    if is_admin:
        edited_f = st.data_editor(df_f, num_rows="dynamic", key="force_edit_table")
        if st.button("භට පිරිස් දත්ත Update කරන්න"):
            df_f.to_sql('force_details', conn, if_exists='replace', index=False)
            st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")
    else:
        st.dataframe(df_f)
    conn.close()

# --- TAB 4: Summary ---
with tab4:
    st.subheader("📊 කලාපීය/සේනාංක සාරාංශය")
    # මෙතනදී මුළු එකතුව පෙන්වනවා
    if not df_f.empty:
        summary = df_f.groupby('category').sum().reset_index()
        st.table(summary[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PC', 'row_total']])

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
