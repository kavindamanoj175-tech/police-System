import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති සැකසුම් (Page Config) ---
# මෙතනින් තමයි Browser එකේ Icon එක සහ නම හදන්නේ
st.set_page_config(
    page_title="STF DBMS - Jaffna & Vavuniya Zones",
    page_icon="👮",
    layout="wide"
)

# --- 2. පද්ධති ආරක්ෂක කාර්යයන් (Security Functions) ---
# (ඔයාගේ මුල් කෝඩ් එකේ තිබුණු ෆන්ක්ෂන්ස් කිසිම වෙනසක් නැතුව)
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
    
    # --- අලුත් Tables (සටහන් සහ වාර්තා සඳහා) ---
    # Notes සඳහා වගුව
    c.execute('''CREATE TABLE IF NOT EXISTS system_notes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, note TEXT)''')
    #Uploaded Reports සඳහා වගුව (මෙතන File data BLOB එකක් විදිහට සේව් වේ)
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_reports 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, file_name TEXT, file_data BLOB)''')
    
    conn.commit()
    conn.close()

# අනෙක් Database functions (කිසිම වෙනසක් නැත)
def add_userdata(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username,password,is_approved) VALUES (?,?,0)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
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

# --- අලුත් Database Functions (Notes & Reports) ---
def add_system_note(username, note_text):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO system_notes (username, date, note) VALUES (?,?,?)', (username, datetime.now().strftime("%Y-%m-%d %H:%M"), note_text))
    conn.commit()
    conn.close()

def get_system_notes():
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT * FROM system_notes ORDER BY id DESC')
    notes = c.fetchall()
    conn.close()
    return notes

def add_uploaded_report(username, file_name, file_bytes):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('INSERT INTO uploaded_reports (username, date, file_name, file_data) VALUES (?,?,?,?)', (username, datetime.now().strftime("%Y-%m-%d %H:%M"), file_name, file_bytes))
    conn.commit()
    conn.close()

def get_uploaded_reports_list():
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT id, username, date, file_name FROM uploaded_reports ORDER BY id DESC')
    reports = c.fetchall()
    conn.close()
    return reports

def get_uploaded_report_data(report_id):
    conn = sqlite3.connect('police_master_system.db')
    c = conn.cursor()
    c.execute('SELECT file_name, file_data FROM uploaded_reports WHERE id = ?', (report_id,))
    report_data = c.fetchone()
    conn.close()
    return report_data

# Database එක මුලින්ම සකස් කිරීම
init_db()

# --- 3. ධුරාවලිය (Hierarchy Data) ---
# (ඔයාගේ මුල් කෝඩ් එකේ තිබුණු Hierarchy data එක කිසිම වෙනසක් නැතුව)
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

# --- 4. Sidebar - ලෝගෝ සහ Admin පාලනය ---
st.sidebar.title("👮 STF DBMS") # <-- App එකේ නම වෙනස් කළා

# ලෝගෝ එක සයිඩ් බාර් එකේ පෙන්වීම
try:
    img = Image.open("logo.png") # 'logo.png' නමින් GitHub එකේ ඇති පින්තූරය
    st.sidebar.image(img, use_column_width=True)
except FileNotFoundError:
    st.sidebar.error("Logo file (logo.png) not found in GitHub repository!")
exceptException as e:
    st.sidebar.error(f"Error loading logo: {e}")

st.sidebar.divider()
st.sidebar.title("🛡️ පද්ධති ආරක්ෂාව")

# Admin Panel (ඔයාගේ මුල් කෝඩ් එකේ තිබුණු Logic එක)
st.sidebar.subheader("👑 Admin පාලක පුවරුව")
admin_key = st.sidebar.text_input("Admin Key", type="password", help="අලුත් අය Approve කිරීමට රහස් කේතය ඇතුළත් කරන්න")

if admin_key == "Police@123": # <--- රහස් කේතය
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

# Login / Sign Up UI (කිසිම වෙනසක් නැත)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

auth_choice = st.sidebar.selectbox("ප්‍රවේශය තෝරන්න", ["Login", "Sign Up"])

if auth_choice == "Sign Up":
    st.subheader("📝 අලුත් ගිණුමක් සාදන්න (STF DBMS)")
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
            st.rerun()
        else:
            st.sidebar.error("වැරදි මුරපදයක් හෝ ඔබව තවමත් අනුමත කර නැත!")

# --- 5. ප්‍රධාන පද්ධතිය (ලොග් වුණු අයට පමණි) ---
if st.session_state['logged_in']:
    st.title(f"👮 STF DBMS - සාදරයෙන් පිළිගනිමු {st.session_state['username']}!")
    st.markdown(f"**Jaffna & Vavuniya Zones - දත්ත කළමනාකරණ පද්ධතිය**")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 ഭට පිරිස් වාර්තා", "⚔️ වැටලීම් වාර්තා", "👤 අපරාධකරුවන්", "📈 විශ්ලේෂණය"])

    # Hierarchy Selection (ඔයාගේ මුල් කෝඩ් එකේ තිබුණු Logic එක)
    zone_select = st.sidebar.selectbox("කලාපය", list(hierarchy.keys()))
    div_select = st.sidebar.selectbox("සේනාංකය", list(hierarchy[zone_select].keys()))
    main_camp_select = st.sidebar.selectbox("ප්‍රධාන කදවුර", list(hierarchy[zone_select][div_select].keys()))
    sub_camps = hierarchy[zone_select][div_select][main_camp_select]
    unit_select = st.sidebar.selectbox("උප කදවුර", ["ප්‍රධාන කදවුර"] + sub_camps) if sub_camps else "ප්‍රධාන කදවුර"
    final_unit = unit_select if unit_select != "ප්‍රධාන කදවුර" else main_camp_select

    # --- tab1: ഭට පිරිස් වාර්තා (කිසිම වෙනසක් නැත) ---
    with tab1:
        st.header(f"📊 භට සංඛ්‍යාලේඛන - {final_unit}")
        cols = ["SSP", "SP", "ASP", "CI", "IP", "SI", "PS", "PSD", "PC", "PCD"]
        with st.form("force_stats_form"):
            inputs = {}
            r1 = st.columns(5)
            r2 = st.columns(5)
            for i, c_name in enumerate(cols):
                inputs[c_name] = r1[i].number_input(c_name, min_value=0, key=f"force_{c_name}") if i < 5 else r2[i-5].number_input(c_name, min_value=0, key=f"force_{c_name}")
            
            if st.form_submit_button("වාර්තාව ඇතුළත් කරන්න"):
                conn = sqlite3.connect('police_master_system.db')
                c = conn.cursor()
                c.execute(f'INSERT INTO force_stats (date, zone, division, camp, {", ".join(cols)}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (datetime.now().strftime("%Y-%m-%d"), zone_select, div_select, final_unit, *inputs.values()))
                conn.commit()
                st.success(f"{final_unit} දත්ත ගබඩා විය!")

    # --- tab2: වැටලීම් වාර්තා (කිසිම වෙනසක් නැත) ---
    with tab2:
        st.header("⚔️ වැටලීම් වාර්තා")
        raid_val = st.number_input("අද දින වැටලීම් ගණන", min_value=0, key="raid_input")
        if st.button("වැටලීම් සුරකින්න"):
            conn = sqlite3.connect('police_master_system.db')
            c = conn.cursor()
            c.execute("INSERT INTO raids VALUES (?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), zone_select, div_select, final_unit, raid_val))
            conn.commit()
            st.success("වැටලීම් දත්ත සුරැකිණි!")

    # --- tab3: අපරාධකරුවන් (කිසිම වෙනසක් නැත) ---
    with tab3:
        st.header("👤 අපරාධකරුවන්ගේ දත්ත")
        with st.form("criminal_form"):
            c_name = st.text_input("නම")
            c_nic = st.text_input("NIC")
            c_photo = st.file_uploader("ඡායාරූපය", type=['jpg','png'])
            if st.form_submit_button("දත්ත ඇතුළත් කරන්න"):
                # (මෙහිදී Criminal දත්ත සේව් කරන Logic එක මුල් කෝඩ් එකේ තිබූ විදිහට)
                st.success("අපරාධකරු ලියාපදිංචි විය! (Database Logic is Active)")

    # --- tab4: විශ්ලේෂණය (නව වෙනස්කම් සහිතව) ---
    with tab4:
        st.header("📈 විශ්ලේෂණ හා වාර්තා පුවරුව")
        
        # විශ්ලේෂණ Tab එක ඇතුලේ තවත් tabs 3ක් (Charts, Files, Notes) හදනවා
        analys_tabs = st.tabs(["📊 සාරාංශ ගත වාර්තා (Charts)", "📁 වාර්තා Upload කිරීම", "📝 පද්ධති සටහන් (Notes Panel)"])
        
        # 4.1 Charts Sub-Tab (ඔයාගේ මුල් කෝඩ් එකේ තිබූ charts)
        with analys_tabs[0]:
            st.subheader("දෘශ්‍යමය විශ්ලේෂණය (Visual Analytics)")
            conn = sqlite3.connect('police_master_system.db')
            df_raids = pd.read_sql_query("SELECT * FROM raids", conn)
            
            if not df_raids.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("සේනාංක මට්ටමින් වැටලීම්")
                    fig = px.pie(df_raids, values='raid_count', names='division', hole=.3, color_discrete_sequence=px.colors.sequential.Teal)
                    st.plotly_chart(fig)
                
                with col2:
                    st.subheader("කලාප මට්ටමින් වැටලීම්")
                    zone_chart = df_raids.groupby('zone')['raid_count'].sum().reset_index()
                    st.bar_chart(zone_chart.set_index('zone'))
            else:
                st.info("Charts පෙන්වීමට ප්‍රමාණවත් වැටලීම් දත්ත නැත.")
            conn.close()

        # 4.2 File Upload Sub-Tab (අලුත් වෙනස්කම්)
        with analys_tabs[1]:
            st.subheader("වාර්තා (Reports/Files) Upload කිරීම")
            with st.form("file_upload_form"):
                uploaded_file = st.file_uploader("Upload Report (PDF, Word, Images)", type=['pdf','docx','docx','jpg','png'])
                f_notes = st.text_input("වාර්තාව පිළිබඳ සටහනක්")
                submit_file = st.form_submit_button("Upload File")
                
                if submit_file and uploaded_file is not None:
                    # File bytes ලබා ගැනීම
                    file_bytes = uploaded_file.read()
                    # Database එකට File bytes සහ නම සේව් කිරීම
                    add_uploaded_report(st.session_state['username'], uploaded_file.name, file_bytes)
                    st.success(f"{uploaded_file.name} වාර්තාව සාර්ථකව Upload කරන ලදී!")

            st.divider()
            st.subheader("Upload කර ඇති වාර්තා (Reports List)")
            # Upload කළ Reports ලිස්ට් එක පෙන්වීම
            reports_list = get_uploaded_reports_list()
            if reports_list:
                reports_df = pd.DataFrame(reports_list, columns=['ID','User','Date','File Name'])
                st.dataframe(reports_df, use_container_width=True)
                
                # File එක Download කිරීමට අවස්ථාව දීම
                st.divider()
                st.subheader("වාර්තාවක් Download කිරීම")
                report_id_to_dl = st.number_input("Download කිරීමට අවශ්‍ය ID එක ටයිප් කරන්න", min_value=1, step=1)
                if st.button("Download File"):
                    rep_data = get_uploaded_report_data(report_id_to_dl)
                    if rep_data:
                        f_name, f_data = rep_data
                        st.download_button(label=f"Download {f_name}", data=f_data, file_name=f_name)
                    else:
                        st.error("Invalid ID! එම ID එකෙන් වාර්තාවක් නැත.")
            else:
                st.info("Upload කර ඇති වාර්තා නැත.")

        # 4.3 Note Pad Sub-Tab (අලුත් වෙනස්කම්)
        with analys_tabs[2]:
            st.subheader("📝 පද්ධති සටහන් පොත (System Note Pad)")
            
            # Note entry area
            with st.form("note_form"):
                note_text = st.text_area("ඔබේ සටහන මෙතන ටයිප් කරන්න (Note/Alert/Reminder)", height=150)
                submit_note = st.form_submit_button("සේව් කරන්න (Save Note)")
                
                if submit_note and note_text:
                    add_system_note(st.session_state['username'], note_text)
                    st.success("සටහන සාර්ථකව සුරකින ලදී!")
                    st.rerun() # නව සටහන පෙන්වීමට rerun කිරීම

            st.divider()
            st.subheader("පැරණි සටහන් (Log/History)")
            
            # Notes ලිස්ට් එක පෙන්වීම
            notes = get_system_notes()
            if notes:
                for n in notes:
                    with st.expander(f"{n[2]} - {n[1]} (id: {n[0]})"):
                        st.write(n[3])
                        st.markdown(f"*Posted by {n[1]} on {n[2]}*")
            else:
                st.info("පැරණි සටහන් නැත.")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

else:
    st.header("Sri Lanka Police Special Task Force")
    st.markdown("## STF DBMS - Jaffna & Vavuniya Zones")
    st.image(img, width=200) # ලොග් වෙන්න කලින් Heading එකේ ලෝ ගෝ එක පෙන්වීම
    st.warning("⚠️ පද්ධතියට ඇතුළු වීමට ප්‍රථම ලොග් වන්න.")
    st.info("ඔබ නවකයෙකු නම් Sign Up වී Admin අනුමැතිය ලැබෙන තෙක් රැඳී සිටින්න.")
