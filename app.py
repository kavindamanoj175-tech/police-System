import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
from PIL import Image

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Security Data Management",
    page_icon="👮",
    layout="wide"
)

# --- Navigation Logic (Fixing the Sync Issue) ---
tabs_list = ["📝 වැටලීම් ඇතුළත් කිරීම", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා (Edit/Delete)", "📊 සාරාංශ පිරික්සුම"]

if 'nav_selection' not in st.session_state:
    st.session_state['nav_selection'] = tabs_list[0]

# බටන් ක්ලික් කළාම සෙලෙක්ෂන් එක මාරු කරන ෆන්ක්ෂන් එක
def update_nav(index):
    st.session_state['nav_selection'] = tabs_list[index]

# --- 2. Database Init ---
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
                  SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. ධුරාවලිය (Hierarchy) ---
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

# --- 4. Sidebar ---
st.sidebar.title("👮 STF DBMS")
try:
    img = Image.open("logo.png")
    st.sidebar.image(img, use_container_width=True)
except:
    st.sidebar.info("Logo not found.")

# Home & Nav Buttons (Fixing Logic)
col_h1, col_h2, col_h3 = st.sidebar.columns(3)
current_idx = tabs_list.index(st.session_state['nav_selection'])

if col_h1.button("🏠 Home"):
    update_nav(0)
    st.rerun()

if col_h2.button("⬅️ Back"):
    if current_idx > 0:
        update_nav(current_idx - 1)
        st.rerun()

if col_h3.button("➡️ Fwd"):
    if current_idx < len(tabs_list) - 1:
        update_nav(current_idx + 1)
        st.rerun()

# YouTube Button
st.sidebar.markdown("---")
yt_url = "https://www.youtube.com/@STF_SriLanka"
st.sidebar.link_button("📺 YouTube Live / CCTV", yt_url, use_container_width=True)
st.sidebar.divider()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Access"):
        st.session_state['logged_in'] = True; st.session_state['username'] = u; st.rerun()
    st.stop()

# Dropdowns
zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key = st.sidebar.text_input("Admin Key", type="password")
is_admin = (admin_key == "Police@123")

# --- 5. Main Navigation (Synchronized) ---
# මෙතන තමයි වැදගත්ම දේ. Radio එකේ index එක session state එකට link කළා.
current_tab = st.radio("Navigation", tabs_list, 
                       index=tabs_list.index(st.session_state['nav_selection']), 
                       horizontal=True, 
                       key="radio_nav",
                       on_change=lambda: st.session_state.update(nav_selection=st.session_state.radio_nav))

# --- TAB CONTENTS ---

if st.session_state['nav_selection'] == "📝 වැටලීම් ඇතුළත් කිරීම":
    st.subheader(f"වැටලීම් වාර්තාව - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
        k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", 0.0)
        heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
        tablet = c4.number_input("මත් කරල් - ග්‍රෑම්", 0.0)
        liq = c1.number_input("මත්පැන් (මිලි ලීටර්)”, 0.0)
        goda = c2.number_input("ගෝඩා (ලීටර්)", 0.0)
        sand = c3.number_input("වැලි වැටලීම්", 0.0)
        wood = c4.number_input(“දැව වැටලීම්", 0.0)
        suspects = c1.number_input("සැකකරුවන්", 0)
        other_txt = st.text_area("අමතර විස්තර සහ වෙනත් වැටලීම්")
        if st.form_submit_button("දත්ත සුරකින්න"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, අයිස්, kerala_ganja, heroin, illegal_liquor, goda, sand_timber, suspects, other_records) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, liq, goda, sand, suspects, other_txt))
            conn.commit(); conn.close(); st.success("සාර්ථකව සුරැකිණි!")

elif st.session_state['nav_selection'] == "📉 භට පිරිස් දත්ත":
    st.subheader(f"භට පිරිස් දත්ත - {sub_camp}")
    with st.form("force_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි", "02 නිවාඩු/විවේක"])
        if st.form_submit_button("යාවත්කාලීන කරන්න"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            total = ssp+sp+asp+ci+ip+si+ps+pc
            c.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, total))
            conn.commit(); conn.close(); st.success("භට පිරිස් දත්ත සුරැකිණි!")

elif st.session_state['nav_selection'] == "🔍 වාර්තා (Edit/Delete)":
    st.subheader("🔍 දත්ත කළමනාකරණය")
    conn = sqlite3.connect('police_master_system.db')
    df_r = pd.read_sql_query(f"SELECT * FROM detailed_raids WHERE zone='{zone_sel}'", conn)
    if is_admin:
        edited_r = st.data_editor(df_r, num_rows="dynamic", key="raid_ed")
        if st.button("Update Raid Database"):
            edited_r.to_sql('detailed_raids', conn, if_exists='replace', index=False)
            st.success("වැටලීම් දත්ත යාවත්කාලීන විය!"); st.rerun()
    else:
        st.dataframe(df_r)
    conn.close()

elif st.session_state['nav_selection'] == "📊 සාරාංශ පිරික්සුම":
    st.subheader("📊 කලාපීය/සේනාංක සාරාංශ පිරික්සුම")
    conn = sqlite3.connect('police_master_system.db')
    df_f = pd.read_sql_query(f"SELECT * FROM force_details WHERE zone='{zone_sel}'", conn)
    if not df_f.empty:
        if is_admin:
            edited_f = st.data_editor(df_f, num_rows="dynamic", key="summary_ed")
            if st.button("Update Force Database"):
                edited_f.to_sql('force_details', conn, if_exists='replace', index=False)
                st.success("දත්ත යාවත්කාලීන විය!"); st.rerun()
        else:
            summary = df_f.groupby('category').sum().reset_index()
            st.table(summary[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PC', 'row_total']])
    conn.close()

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
