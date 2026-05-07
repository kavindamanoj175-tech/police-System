import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image
import io
import plotly.express as px

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Strategic Data System",
    page_icon="👮",
    layout="wide"
)

# --- Navigation Logic ---
tabs_list = [
    "📝 වැටලීම් ඇතුළත් කිරීම", 
    "📉 භට පිරිස් දත්ත", 
    "🔍 වාර්තා පිරික්සුම", 
    "📊 සාරාංශ සහ සිතියම්", 
    "🔫 අවි ආයුධ සහ වාහන", 
    "📅 දෛනික රාජකාරි ලේඛනය",
    "🕵️ Intelligence Log"
]

if 'nav_selection' not in st.session_state:
    st.session_state['nav_selection'] = tabs_list[0]

def update_nav(index):
    st.session_state['nav_selection'] = tabs_list[index]

# --- 2. Database Init (Fixed Column Error) ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    # මෙතන තමයි වැදගත්ම කොටස - අලුත් හැම column එකක්ම මෙතන තියෙනවා
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, tablet REAL, 
                  illegal_liquor REAL, goda REAL, sand REAL, wood REAL,
                  suspects INTEGER, suspect_name TEXT, other_records TEXT, 
                  location TEXT, court_date TEXT, case_no TEXT, 
                  image_blob BLOB, lat REAL, lon REAL)''')
    
    c.execute('CREATE TABLE IF NOT EXISTS force_details (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT, category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS intel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, info TEXT, priority TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS weapon_inv (id INTEGER PRIMARY KEY AUTOINCREMENT, weapon_type TEXT, amunition_count INTEGER, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS duty_roster (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, officer_name TEXT, duty_type TEXT, location TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS vehicle_log (id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_no TEXT, status TEXT, last_service TEXT)')
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

col_h1, col_h2, col_h3 = st.sidebar.columns(3)
if col_h1.button("🏠 Home"): update_nav(0); st.rerun()
if col_h2.button("⬅️ Back"):
    idx = tabs_list.index(st.session_state['nav_selection'])
    if idx > 0: update_nav(idx - 1); st.rerun()
if col_h3.button("➡️ Fwd"):
    idx = tabs_list.index(st.session_state['nav_selection'])
    if idx < len(tabs_list) - 1: update_nav(idx + 1); st.rerun()

st.sidebar.markdown("---")
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    u = st.sidebar.text_input("User Name")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Access"): st.session_state['logged_in'] = True; st.rerun()
    st.stop()

zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key = st.sidebar.text_input("Admin Key", type="password")
is_admin = (admin_key == "Police@123")

# Navigation Control
available_tabs = tabs_list if is_admin else tabs_list[:-1]
current_tab = st.radio("Navigation", available_tabs, index=available_tabs.index(st.session_state['nav_selection']) if st.session_state['nav_selection'] in available_tabs else 0, horizontal=True, key="radio_nav")
st.divider()

# --- TAB 1: Raid Entry ---
if st.session_state.radio_nav == "📝 වැටලීම් ඇතුළත් කිරීම":
    st.subheader(f"📝 වැටලීම් වාර්තාව - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
        k_ganja = c2.number_input("කේරළ ගංජා - ග්‍රෑම්", 0.0)
        heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
        tablet = c4.number_input("මත් කරල්", 0.0)
        
        st.write("---")
        s_name = st.text_input("සැකකරුගේ නම")
        location = st.text_input("ස්ථානය (ගම/ප්‍රදේශය)")
        lat = st.number_input("Latitude", format="%.6f", value=6.9271)
        lon = st.number_input("Longitude", format="%.6f", value=79.8612)
        other_txt = st.text_area("අමතර සටහන්")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            conn = sqlite3.connect('police_master_system.db'); c = conn.cursor()
            c.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, tablet, suspects, suspect_name, other_records, location, lat, lon) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                      (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, tablet, 1 if s_name else 0, s_name, other_txt, location, lat, lon))
            conn.commit(); conn.close(); st.success("සාර්ථකයි!")

# --- TAB 4: Maps & Analytics (Fixing the Error) ---
elif st.session_state.radio_nav == "📊 සාරාංශ සහ සිතියම්":
    st.subheader("📍 වැටලීම් සිතියම")
    conn = sqlite3.connect('police_master_system.db')
    try:
        # Error එක එන තැන මෙතනයි - මම මේක Try/Except දාලා ආරක්ෂිත කළා
        df_map = pd.read_sql_query("SELECT lat, lon, suspect_name, location FROM detailed_raids", conn)
        if not df_map.empty:
            st.map(df_map)
        else:
            st.info("සිතියමේ පෙන්වීමට තවමත් දත්ත නොමැත.")
    except Exception as e:
        st.error("Database structure එකේ ගැටලුවක් තියෙනවා. කරුණාකර Reboot කරන්න.")
    
    st.write("---")
    # Graphs
    df_all = pd.read_sql_query("SELECT ice, kerala_ganja, heroin FROM detailed_raids", conn)
    if not df_all.empty:
        fig = px.bar(df_all.sum().reset_index(), x='index', y=0, title="මත්ද්‍රව්‍ය වැටලීම් සාරාංශය", labels={'index':'වර්ගය', '0':'ප්‍රමාණය'})
        st.plotly_chart(fig)
    conn.close()

# අනිත් ටැබ් ටිකත් මේ විදිහටම තියෙනවා...
elif st.session_state.radio_nav == "🔍 වාර්තා පිරික්සුම":
    conn = sqlite3.connect('police_master_system.db')
    st.dataframe(pd.read_sql_query("SELECT * FROM detailed_raids", conn))
    conn.close()

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False; st.rerun()
