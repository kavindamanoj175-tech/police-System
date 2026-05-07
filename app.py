import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from PIL import Image
import io

# --- 1. පද්ධති සැකසුම් ---
st.set_page_config(page_title="STF DBMS - Master Pro", page_icon="👮", layout="wide")

# --- 2. Google Sheets සම්බන්ධතාවය ---
# මෙය වැඩ කිරීමට Secrets වල spreadsheet link එක තිබිය යුතුය.
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. Sidebar & Security ---
st.sidebar.title("👮 STF DBMS")
try:
    img = Image.open("logo.png")
    st.sidebar.image(img, use_column_width=True)
except:
    st.sidebar.info("Logo file not found.")

if 'logged_in' not in st.session_state: 
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.sidebar.subheader("Login Area")
    u = st.sidebar.text_input("Username")
    p = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        if u == "admin" and p == "stf123": # අවශ්‍ය පරිදි වෙනස් කරන්න
            st.session_state['logged_in'] = True
            st.rerun()
        else: 
            st.sidebar.error("වැරදි දත්ත!")
    st.stop() # ලොග් වන තෙක් ඉතිරි කෝඩ් එක දුවන්නේ නැත.

# --- 4. Main App (ලොග් වූ පසු) ---
st.title("🚨 Special Task Force - Data Management System")

# Global Selections
zone_sel = st.sidebar.selectbox("කලාපය", ["යාපනය කලාපය", "වව්නියාව කලාපය"])
camp_sel = st.sidebar.text_input("කදවුර / උප කදවුර", value="වි.කා.බ යාපනය")

tab1, tab2, tab3 = st.tabs(["📊 භට පිරිස් වාර්තා", "⚔️ වැටලීම් වාර්තා", "🔍 වාර්තා කළමනාකරණය (Delete)"])

# --- TAB 1: භට පිරිස් වාර්තා ---
with tab1:
    st.header(f"📊 භට සංඛ්‍යාලේඛන ඇතුළත් කිරීම - {camp_sel}")
    with st.form("force_form", clear_on_submit=True):
        cols_list = ["SSP", "SP", "ASP", "CI", "IP", "SI", "PS", "PSD", "PC", "PCD"]
        inputs = {}
        r1 = st.columns(5)
        r2 = st.columns(5)
        for i, name in enumerate(cols_list):
            if i < 5: inputs[name] = r1[i].number_input(name, min_value=0)
            else: inputs[name] = r2[i-5].number_input(name, min_value=0)
        
        if st.form_submit_button("භට වාර්තාව සුරකින්න"):
            new_f_data = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Zone": zone_sel, "Camp": camp_sel, **inputs}])
            try:
                old_df = conn.read(worksheet="Force_Stats", ttl=0)
                updated_df = pd.concat([old_df, new_f_data], ignore_index=True)
                conn.update(worksheet="Force_Stats", data=updated_df)
                st.success("භට පිරිස් වාර්තාව සාර්ථකව Google Sheet එකට එකතු කළා!")
            except: st.error("Google Sheet එකේ 'Force_Stats' Tab එක පරීක්ෂා කරන්න.")

# --- TAB 2: වැටලීම් වාර්තා ---
with tab2:
    st.header(f"⚔️ වැටලීම් වාර්තා ඇතුළත් කිරීම - {camp_sel}")
    with st.form("raid_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ice = c1.number_input("අයිස් (ග්‍රෑම්)", 0.0)
        kg = c2.number_input("කේරළ ගංජා (කි.ග්‍රෑ)", 0.0)
        hr = c3.number_input("හෙරොයින් (ග්‍රෑම්)", 0.0)
        liq = c1.number_input("මත්පැන් (බෝතල්)", 0.0)
        sus = c2.number_input("සැකකරුවන් ගණන", 0)
        notes = st.text_area("වෙනත් සටහන්")
        
        if st.form_submit_button("වැටලීම් වාර්තාව සුරකින්න"):
            new_r_data = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"), "Zone": zone_sel, "Camp": camp_sel,
                "ICE": ice, "K_Ganja": kg, "Heroin": hr, "Liquor": liq, "Suspects": int(sus), "Notes": notes
            }])
            try:
                old_df = conn.read(worksheet="Raid_Reports", ttl=0)
                updated_df = pd.concat([old_df, new_r_data], ignore_index=True)
                conn.update(worksheet="Raid_Reports", data=updated_df)
                st.success("වැටලීම් වාර්තාව සාර්ථකව Google Sheet එකට එකතු කළා!")
            except: st.error("Google Sheet එකේ 'Raid_Reports' Tab එක පරීක්ෂා කරන්න.")

# --- TAB 3: Filter, Download & DELETE (අලුත් කොටස) ---
with tab3:
    st.header("🔍 වාර්තා කළමනාකරණය සහ දත්ත මැකීම")
    
    data_type = st.radio("දත්ත වර්ගය තෝරන්න", ["භට පිරිස් (Force_Stats)", "වැටලීම් (Raid_Reports)"], horizontal=True)
    sheet_name = "Force_Stats" if "භට පිරිස්" in data_type else "Raid_Reports"
    
    try:
        # Google Sheet එකෙන් දත්ත කියවීම
        df = conn.read(worksheet=sheet_name, ttl=0)
        
        if not df.empty:
            st.subheader(f"දැනට පවතින {data_type} ලැයිස්තුව")
            st.write("මකන්න අවශ්‍ය පේළියේ අංකය (Index) වම් පැත්තෙන් බලාගන්න.")
            st.dataframe(df, use_container_width=True)
            
            # Excel Download Button
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, header=True, engine='xlsxwriter')
            st.download_button("📥 සම්පූර්ණ වාර්තාව Excel ලෙස බාගත කරන්න", data=towrite.getvalue(), file_name=f"{sheet_name}_Report.xlsx")

            # --- DELETE SECTION ---
            st.divider()
            st.subheader("🗑️ වාර්තාවක් මකා දැමීම")
            row_idx = st.number_input("මැකීමට අවශ්‍ය පේළි අංකය (Row Index) ඇතුළත් කරන්න", min_value=0, max_value=len(df)-1, step=1)
            
            if st.button("තෝරාගත් පේළිය සදහටම මකන්න", type="primary"):
                # පේළිය ඉවත් කිරීම
                updated_df = df.drop(df.index[row_idx])
                # Google Sheet එක Update කිරීම
                conn.update(worksheet=sheet_name, data=updated_df)
                st.warning(f"පේළි අංක {row_idx} සාර්ථකව මකා දැමුවා!")
                st.rerun() # Refresh app
        else:
            st.info("දැනට දත්ත කිසිවක් ගබඩා කර නැත.")
    except Exception as e:
        st.error(f"දෝෂයක් පවතී: {e}")

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()
