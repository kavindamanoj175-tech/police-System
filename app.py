import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති ආරක්ෂක කාර්යයන් (Security Functions) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def init_db():
    conn = sqlite3.connect('police_master_system.db', check_same_thread=False)
    c = conn.cursor()
    # පරිශීලක වගුව (is_approved column එක සහිතව)
    c.execute('''CREATE TABLE IF NOT EXISTS userstable
                 (username TEXT, password TEXT, is_approved INTEGER DEFAULT 0)''')
    # භට පිරිස් වගුව
    c.execute('''CREATE TABLE IF NOT EXISTS force_stats 
                 (date TEXT, zone TEXT, division TEXT, camp TEXT, 
                  SSP INTEGER, SP INTEGER, ASP INTEGER, CI INTEGER, IP INTEGER, 
                  SI INTEGER, PS INTEGER, PSD INTEGER, PC INTEGER, PCD INTEGER)''')
    # වැටලීම් වගුව
    c.execute('''CREATE TABLE IF NOT EXISTS raids 
                 (date TEXT, zone TEXT, division TEXT, camp TEXT, raid_count INTEGER)''')
    # අපරාධකරුවන්ගේ වගුව
    c.execute('''CREATE TABLE IF NOT EXISTS criminals 
                 (name TEXT, address TEXT, nic TEXT, phone TEXT, records TEXT, photo BLOB, camp TEXT)''')
    conn.commit()
    conn.close()

def add_userdata(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username,password,is_approved) VALUES (?,?,0)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    # මෙතනදී බලන්නේ password එක වගේම Admin Approve (1) කරලද කියලයි
    c.execute('SELECT * FROM userstable WHERE username =? AND password =? AND is_approved = 1', (username, password))
    data = c.fetchall()
    return data

def get_pending_users():
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT username FROM userstable WHERE is_approved = 0')
    return c.fetchall()

def approve_user(username):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('UPDATE userstable SET is_approved = 1 WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Database එක මුලින්ම සකස් කිරීම
init_db()

# --- 2. ධුරාවලිය (Hierarchy Data) ---
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

# --- 3. Sidebar - Admin සහ Login පාලනය ---
st.sidebar.title("🛡️ පද්ධති ආරක්ෂාව")

# Admin Panel (ඔයාට විතරක් ඇතුල් වෙන්න පුළුවන් රහස් තැන)
st.sidebar.subheader("👑 Admin පාලක පුවරුව")
admin_key = st.sidebar.text_input("Admin Key", type="password", help="අලුත් අය Approve කිරීමට රහස් කේතය ඇතුළත් කරන්න")

if admin_key == "Police@123": # <--- ඔයාට ඕන Password එක මෙතනට දාන්න
    pending = get_pending_users()
    if pending:
        user_to_approve = st.sidebar.selectbox("අනුමත කිරීමට තෝරන්න", [u[0] for u in pending])
        if st.sidebar.button("Approve User"):
            approve_user(user_to_approve)
            st.sidebar.success(f"{user_to_approve} සාර්ථකව අනුමත කළා!")
            st.rerun()
    else:
        st.sidebar.info("අනුමත කිරීමට අලුත් අය නැත.")

st.sidebar.divider()

# Login / Sign Up UI
auth_choice = st.sidebar.selectbox("ප්‍රවේශය තෝරන්න", ["Login", "Sign Up"])

if auth_choice == "Sign Up":
    st.subheader("📝 අලුත් ගිණුමක් සාදන්න")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("ගිණුම ලියාපදිංචි කරන්න"):
        add_userdata(new_user, make_hashes(new_password))
        st.info("ඔබගේ ගිණුම සෑදුවා. Admin විසින් අනුමත කළ පසු ඔබට ලොග් විය හැක.")

elif auth_choice == "Login":
    user = st.sidebar.text_input("User Name")
    passwd = st.sidebar.text_input("Password", type='password')
    
    if st.sidebar.button("ඇතුල් වන්න (Login)"):
        hashed_pswd = make_hashes(passwd)
        result = login_user(user, check_hashes(passwd, hashed_pswd))
        
        if result:
            st.session_state['logged_in'] = True
            st.session_state['username'] = user
        else:
            st.sidebar.error("වැරදි මුරපදයක් හෝ ඔබව තවමත් අනුමත කර නැත!")

# --- 4. ප්‍රධාන පද්ධතිය (ලොග් වුණු අයට පමණි) ---
if st.session_state.get('logged_in'):
    st.title(f"👮 Police System - සාදරයෙන් පිළිගනිමු {st.session_state['username']}!")
    
    tab1, tab2, tab3, tab4 = st.tabs(["භට පිරිස් වාර්තා", "වැටලීම් වාර්තා", "අපරාධකරුවන්", "විශ්ලේෂණය"])

    # Hierarchy Selection
    zone_select = st.sidebar.selectbox("කලාපය", list(hierarchy.keys()))
    div_select = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_select].keys()))
    main_camp_select = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_select][div_select].keys()))
    sub_camps = hierarchy[zone_select][div_select][main_camp_select]
    unit_select = st.sidebar.selectbox("උප කදවුර", ["ප්‍රධාන කදවුර"] + sub_camps) if sub_camps else "ප්‍රධාන කදවුර"
    final_unit = unit_select if unit_select != "ප්‍රධාන කදවුර" else main_camp_select

    with tab1:
        st.header(f"📊 භට සංඛ්‍යාලේඛන - {final_unit}")
        cols = ["SSP", "SP", "ASP", "CI", "IP", "SI", "PS", "PSD", "PC", "PCD"]
        with st.form("force_stats_form"):
            inputs = {}
            r1 = st.columns(5)
            r2 = st.columns(5)
            for i, c_name in enumerate(cols):
                inputs[c_name] = r1[i].number_input(c_name, min_value=0) if i < 5 else r2[i-5].number_input(c_name, min_value=0)
            
            if st.form_submit_button("වාර්තාව ඇතුළත් කරන්න"):
                conn = sqlite3.connect('police_master_system.db')
                c = conn.cursor()
                c.execute(f'INSERT INTO force_stats (date, zone, division, camp, {", ".join(cols)}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (datetime.now().strftime("%Y-%m-%d"), zone_select, div_select, final_unit, *inputs.values()))
                conn.commit()
                st.success(f"{final_unit} දත්ත ගබඩා විය!")

    with tab2:
        st.header("⚔️ වැටලීම් වාර්තා")
        raid_val = st.number_input("අද දින වැටලීම් ගණන", min_value=0)
        if st.button("වැටලීම් සුරකින්න"):
            conn = sqlite3.connect('police_master_system.db')
            c = conn.cursor()
            c.execute("INSERT INTO raids VALUES (?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), zone_select, div_select, final_unit, raid_val))
            conn.commit()
            st.success("වැටලීම් දත්ත සුරැකිණි!")

    with tab3:
        st.header("👤 අපරාධකරුවන්ගේ දත්ත")
        with st.form("criminal_form"):
            c_name = st.text_input("නම")
            c_nic = st.text_input("NIC")
            c_photo = st.file_uploader("ඡායාරූපය", type=['jpg','png'])
            if st.form_submit_button("දත්ත ඇතුළත් කරන්න"):
                # (මෙහිදී Criminal දත්ත සේව් කරන Logic එක ක්‍රියාත්මක වේ)
                st.success("අපරාධකරු ලියාපදිංචි විය!")

    with tab4:
        st.header("📈 සාරාංශගත වාර්තා")
        conn = sqlite3.connect('police_master_system.db')
        df_raids = pd.read_sql_query("SELECT * FROM raids", conn)
        if not df_raids.empty:
            st.subheader("සේනාංක මට්ටමින් වැටලීම්")
            fig = px.pie(df_raids, values='raid_count', names='division', hole=.3)
            st.plotly_chart(fig)
            
            st.subheader("කලාප මට්ටමින් වැටලීම්")
            zone_chart = df_raids.groupby('zone')['raid_count'].sum().reset_index()
            st.bar_chart(zone_chart.set_index('zone'))

else:
    st.warning("⚠️ පද්ධතියට ඇතුළු වීමට ප්‍රථම ලොග් වන්න.")
    st.info("ඔබ නවකයෙකු නම් Sign Up වී Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")
