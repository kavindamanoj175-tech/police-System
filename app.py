import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(
    page_title="STF - Security Data Management",
    page_icon="👮",
    layout="wide"
)

# Password Hashing
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. Database Functions ---
def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable (username TEXT, password TEXT)')
    # Table එකේ columns සියල්ලම හරියටම මෙතන තියෙනවා
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_raids 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, time TEXT, zone TEXT, division TEXT, camp TEXT,
                  ice REAL, kerala_ganja REAL, heroin REAL, mava REAL, 
                  mandrax REAL, illegal_liquor REAL, goda REAL,
                  sand_timber REAL, suspects INTEGER,
                  other_records TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS force_details 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, zone TEXT, division TEXT, camp TEXT,
                  category TEXT, SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PC INTEGER, row_total INTEGER)''')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    with sqlite3.connect('police_master_system.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
        conn.commit()

def login_user(username, password):
    with sqlite3.connect('police_master_system.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (username, password))
        return c.fetchall()

init_db()

# --- 3. Navigation Logic ---
tabs_list = ["📝 වැටලීම් ඇතුළත් කිරීම", "📉 භට පිරිස් දත්ත", "🔍 වාර්තා (Edit/Delete)", "📊 සාරාංශ පිරික්සුම"]

if 'nav_selection' not in st.session_state:
    st.session_state['nav_selection'] = tabs_list[0]
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 4. Sidebar & Auth ---
st.sidebar.title("👮 STF DBMS")

if not st.session_state['logged_in']:
    auth_mode = st.sidebar.selectbox("තෝරන්න", ["Login", "Sign Up"])
    if auth_mode == "Login":
        u = st.sidebar.text_input("User Name")
        p = st.sidebar.text_input("Password", type='password')
        if st.sidebar.button("Login"):
            result = login_user(u, make_hashes(p))
            if result:
                st.session_state['logged_in'] = True
                st.session_state['username'] = u
                st.rerun()
            else:
                st.sidebar.error("වැරදි පරිශීලක නාමයක් හෝ මුරපදයක්!")
    else:
        new_user = st.sidebar.text_input("Username")
        new_password = st.sidebar.text_input("Password", type='password')
        signup_key = st.sidebar.text_input("Admin Key", type='password')
        if st.sidebar.button("Create Account"):
            if signup_key == "Police@123":
                add_userdata(new_user, make_hashes(new_password))
                st.sidebar.success("සාර්ථකයි! දැන් Login වන්න.")
            else:
                st.sidebar.error("Admin Key වැරදියි!")
    st.stop()

# --- Hierarchy Data ---
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
        }
    }
}

# Sidebar Selectors
zone_sel = st.sidebar.selectbox("පාලන කලාපය", list(hierarchy.keys()))
div_sel = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_sel].keys()))
main_camp = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_sel][div_sel].keys()))
sub_camp = st.sidebar.selectbox("උප කදවුර / ස්ථානය", hierarchy[zone_sel][div_sel][main_camp])

admin_key_input = st.sidebar.text_input("Edit/Delete Admin Key", type="password")
is_admin = (admin_key_input == "Police@123")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 5. Main Content ---
current_tab = st.radio("ප්‍රධාන මෙනුව", tabs_list, 
                       index=tabs_list.index(st.session_state['nav_selection']), 
                       horizontal=True, key="main_nav")
st.session_state['nav_selection'] = current_tab

if current_tab == "📝 වැටලීම් ඇතුළත් කිරීම":
    st.subheader(f"වැටලීම් වාර්තාව - {sub_camp}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        ice = c1.number_input("අයිස් (ICE) - ග්‍රෑම්", 0.0)
        k_ganja = c2.number_input("කේරළ ගංජා - කි.ග්‍රෑ", 0.0)
        heroin = c3.number_input("හෙරොයින් - ග්‍රෑම්", 0.0)
        mandrax = c4.number_input("මත් කරල් - ග්‍රෑම්", 0.0)
        liq = c1.number_input("මත්පැන් (මිලි ලීටර්)", 0.0)
        goda = c2.number_input("ගෝඩා (ලීටර්)", 0.0)
        sand_wood = c3.number_input("වැලි/දැව වැටලීම්", 0.0)
        suspects = c4.number_input("සැකකරුවන්", 0)
        other_txt = st.text_area("අමතර විස්තර")
        
        if st.form_submit_button("දත්ත සුරකින්න"):
            with sqlite3.connect('police_master_system.db') as conn:
                cur = conn.cursor()
                # SQL Injection වලින් ආරක්ෂිතව ඩේටා ඇතුළත් කිරීම
                cur.execute('''INSERT INTO detailed_raids (date, time, zone, division, camp, ice, kerala_ganja, heroin, mandrax, illegal_liquor, goda, sand_timber, suspects, other_records) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                            (datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), zone_sel, div_sel, sub_camp, ice, k_ganja, heroin, mandrax, liq, goda, sand_wood, suspects, other_txt))
                conn.commit()
            st.success("දත්ත සාර්ථකව සුරැකිණි!")

elif current_tab == "📉 භට පිරිස් දත්ත":
    st.subheader(f"භට පිරිස් දත්ත - {sub_camp}")
    with st.form("force_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        ssp = f1.number_input("SSP", 0); sp = f2.number_input("SP", 0); asp = f3.number_input("ASP", 0)
        ci = f1.number_input("CI", 0); ip = f2.number_input("IP", 0); si = f3.number_input("SI", 0)
        ps = f1.number_input("PS", 0); pc = f2.number_input("PC", 0)
        cat = st.selectbox("තත්ත්වය", ["මුළු භට සංඛ්‍යාව", "01 විශේෂ රාජකාරි", "02 නිවාඩු/විවේක"])
        
        if st.form_submit_button("යාවත්කාලීන කරන්න"):
            total = ssp+sp+asp+ci+ip+si+ps+pc
            with sqlite3.connect('police_master_system.db') as conn:
                cur = conn.cursor()
                cur.execute('''INSERT INTO force_details (date, zone, division, camp, category, SSP, SP, ASP, CI, IP, SI, PS, PC, row_total) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                            (datetime.now().strftime("%Y-%m-%d"), zone_sel, div_sel, sub_camp, cat, ssp, sp, asp, ci, ip, si, ps, pc, total))
                conn.commit()
            st.success("භට පිරිස් දත්ත යාවත්කාලීන විය!")

elif current_tab == "🔍 වාර්තා (Edit/Delete)":
    st.subheader(f"🔍 දත්ත පිරික්සුම - {zone_sel}")
    conn = sqlite3.connect('police_master_system.db')
    # Safe Querying
    df_r = pd.read_sql_query("SELECT * FROM detailed_raids WHERE zone=?", conn, params=(zone_sel,))
    
    if is_admin:
        st.info("ඔබට දත්ත සංස්කරණය කළ හැක. වෙනස් කිරීමෙන් පසු 'Update' බොත්තම ඔබන්න.")
        edited_df = st.data_editor(df_r, num_rows="dynamic", key="editor")
        if st.button("Save Changes"):
            # මෙහිදී 'replace' වෙනුවට පරණ ටේබල් එක මකන්නේ නැතිව අප්ඩේට් කිරීම වඩාත් සුදුසුයි
            edited_df.to_sql('detailed_raids', conn, if_exists='replace', index=False)
            st.success("දත්ත යාවත්කාලීන විය!")
            st.rerun()
    else:
        st.warning("සංස්කරණය කිරීමට Admin Key ඇතුළත් කරන්න.")
        st.dataframe(df_r)
    conn.close()

elif current_tab == "📊 සාරාංශ පිරික්සුම":
    st.subheader(f"📊 {zone_sel} සාරාංශය")
    conn = sqlite3.connect('police_master_system.db')
    df_f = pd.read_sql_query("SELECT * FROM force_details WHERE zone=?", conn, params=(zone_sel,))
    if not df_f.empty:
        summary = df_f.groupby('category').sum(numeric_only=True).reset_index()
        st.table(summary[['category', 'SSP', 'SP', 'ASP', 'CI', 'IP', 'SI', 'PS', 'PC', 'row_total']])
    else:
        st.info("දත්ත නොමැත.")
    conn.close()
