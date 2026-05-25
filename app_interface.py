import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Flood Guardian App", layout="wide", page_icon="🌊")

# --- CUSTOM CSS FOR PROFESSIONAL UI ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    
    /* Action Buttons Styling */
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    
    /* Google Maps Link Button Styling */
    .stLinkButton>a {
        background-color: #197AE3 !important;
        color: white !important;
        text-decoration: none;
        display: flex;
        justify-content: center;
        padding: 0.5rem;
        border-radius: 5px;
    }

    /* FIX FOR THE WHITE METRIC BOX VISIBILITY */
    [data-testid="stMetricValue"] { 
        font-size: 35px !important; 
        color: #007bff !important;  
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #333333 !important; 
    }

    /* Styling the regional box to look like a notification card */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# Role Management
if 'role' not in st.session_state:
    st.session_state.role = 'Public User'

st.sidebar.title("🛂 Access Control")
st.session_state.role = st.sidebar.selectbox("Select Role", ["Public User", "Rescue Team"])

# --- DATABASE HELPERS ---
def get_alerts():
    try:
        conn = sqlite3.connect('flood_guardian.db')
        df = pd.read_sql_query("SELECT * FROM alerts ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def update_region_status(location, new_status):
    conn = sqlite3.connect('flood_guardian.db')
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE alerts SET status = ? WHERE location = ?", (new_status, location))
    except:
        cursor.execute("ALTER TABLE alerts ADD COLUMN status TEXT DEFAULT 'Pending'")
        cursor.execute("UPDATE alerts SET status = ? WHERE location = ?", (new_status, location))
    conn.commit()
    conn.close()

# ==========================================
# 🚑 RESCUE TEAM DASHBOARD
# ==========================================
if st.session_state.role == "Rescue Team":
    st.title("🚑 Rescue Operations Command")
    pwd = st.sidebar.text_input("Rescue Authentication Code", type="password")
    
    if pwd == "rescue123":
        if st.sidebar.button("🧹 Reset System Database"):
            conn = sqlite3.connect('flood_guardian.db')
            conn.execute("DELETE FROM alerts")
            conn.commit(); conn.close()
            if os.path.exists("detected_people"):
                for f in os.listdir("detected_people"):
                    os.remove(os.path.join("detected_people", f))
            st.rerun()

        tab_alerts, tab_cctv, tab_team, tab_proof = st.tabs([
            "🚨 Regional Alerts", 
            "📍 CCTV Section", 
            "🚑 Field Personnel", 
            "📜 Proof of Rescue"
        ])

        # --- 1. ALERTS SECTION ---
        with tab_alerts:
            st.subheader("📍 Active Incident Zones")
            df_alerts = get_alerts()
            if not df_alerts.empty:
                active_df = df_alerts[df_alerts['status'].isin(['Pending', 'In Progress'])]
                if not active_df.empty:
                    regions = active_df['location'].unique()
                    for region in regions:
                        region_data = active_df[active_df['location'] == region]
                        total_humans = region_data['person_id'].nunique()
                        status = region_data.iloc[0].get('status', 'Pending')
                        
                        # Card expansion reveals images immediately
                        with st.expander(f"🚩 {region} — {total_humans} Person(s) Spotted (Click to View Images)", expanded=False):
                            col_info, col_gallery = st.columns([1, 2])
                            with col_info:
                                st.metric("Total Humans", total_humans)
                                st.write(f"**Status:** {status}")
                                lat, lon = region_data.iloc[0]['lat'], region_data.iloc[0]['lon']
                                st.write(f"📍 **GPS:** {lat}, {lon}")
                                maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                                st.link_button("🌐 Open in Google Maps", maps_url)
                                st.divider()
                                b1, b2 = st.columns(2)
                                if status == 'Pending':
                                    if b1.button(f"🚀 Deploy Rescue Teams", key=f"acc_{region}"):
                                        update_region_status(region, "In Progress"); st.rerun()
                                if b2.button(f"🏁 Mark Rescued", key=f"comp_{region}"):
                                    update_region_status(region, "Completed"); st.rerun()
                            with col_gallery:
                                st.write("👤 **Identified Individuals:**")
                                img_cols = st.columns(3)
                                for i, (_, row) in enumerate(region_data.iterrows()):
                                    img_path = f"detected_people/person_{row['person_id']}.jpg"
                                    with img_cols[i % 3]:
                                        if os.path.exists(img_path):
                                            st.image(img_path, caption=f"ID: {row['person_id']}", use_container_width=True)
                else:
                    st.success("✅ All regions cleared. No active threats.")
            else:
                st.info("No detections reported yet.")

        # --- 2. CCTV SECTION ---
        with tab_cctv:
            st.subheader("📡 Flood-Prone Camera Network")
            cctv_data = pd.DataFrame([
                {"ID": f"Cam-{i+1:02d}", "Zone": z, "Status": "Active", "Flood Prone": True} 
                for i, z in enumerate(["Puranapul Bridge", "Amberpet Cause Way", "Tolichowki", "Begumpet Nala", 
                                       "Hussain Sagar", "Dilsukhnagar", "Himayat Nagar", "Banjara Hills", 
                                       "Secunderabad Station", "Yousufguda Checkpost", "Malakpet Station"])
            ] + [{"ID": "Cam-12", "Zone": "Hi-Tech City (Safe)", "Status": "Active", "Flood Prone": False}])
            st.table(cctv_data[cctv_data["Flood Prone"] == True][["ID", "Zone", "Status"]])

        # --- 3. FIELD PERSONNEL ---
        with tab_team:
            st.subheader("Field Personnel Availability")
            st.dataframe(pd.DataFrame({
                "Member": ["Commander Ketha", "Officer Rahim", "Unit 4 (Drone)", "Volunteer Group A"],
                "Status": ["Available", "Busy", "Available", "Busy"],
                "Assignment": ["Standby", "Incident #07", "Standby", "Regional Evacuation"]
            }), use_container_width=True)

        # --- 4. PROOF OF RESCUE ---
        with tab_proof:
            st.subheader("✅ Mission History & Proof of Rescue")
            df_alerts = get_alerts()
            if not df_alerts.empty:
                completed_df = df_alerts[df_alerts['status'] == 'Completed']
                if not completed_df.empty:
                    for c_region in completed_df['location'].unique():
                        c_data = completed_df[completed_df['location'] == c_region]
                        st.success(f"🎊 **Successfully Rescued:** {len(c_data)} people from **{c_region}**")
                        proof_cols = st.columns(6) 
                        for i, (_, row) in enumerate(c_data.iterrows()):
                            img_path = f"detected_people/person_{row['person_id']}.jpg"
                            with proof_cols[i % 6]:
                                if os.path.exists(img_path):
                                    st.image(img_path, caption=f"Saved ID: {row['person_id']}", use_container_width=True)
                else:
                    st.info("No completed missions in the log yet.")

    else:
        st.sidebar.error("Unauthorized Access")

# ==========================================
# 🌍 PUBLIC USER DASHBOARD
# ==========================================
else:
    st.title("🌍 Flood Guardian: Public Safety Portal")
    df_alerts = get_alerts() 
    
    if not df_alerts.empty:
        active_threats = df_alerts[df_alerts['status'].isin(['Pending', 'In Progress'])]
        if not active_threats.empty:
            # FIX: Show all active points on map
            st.error(f"⚠️ **URGENT ALERT:** High water activity detected at {len(active_threats['location'].unique())} locations.")
            st.map(active_threats[['lat', 'lon']].drop_duplicates(), zoom=12)
        else:
            st.success("✅ No active flood incidents reported.")
            st.map(pd.DataFrame({'lat': [17.3850], 'lon': [78.4867]}), zoom=11)
    else:
        st.success("✅ System Online: Monitoring Hyderabad.")
        st.map(pd.DataFrame({'lat': [17.3850], 'lon': [78.4867]}), zoom=11)

    st.divider()
    st.subheader("🚩 Monitored High-Risk Danger Zones")
    danger_zones = ["Puranapul Bridge", "Amberpet Cause Way", "Tolichowki", "Begumpet Nala", 
                    "Hussain Sagar", "Dilsukhnagar", "Himayat Nagar", "Banjara Hills", 
                    "Secunderabad Station", "Yousufguda Checkpost", "Malakpet Station"]

    zone_cols = st.columns(3)
    for i, zone in enumerate(danger_zones):
        with zone_cols[i % 3]:
            # Cross-reference with active alerts
            is_danger = not df_alerts[(df_alerts['location'].str.contains(zone[:5])) & (df_alerts['status'] != 'Completed')].empty if not df_alerts.empty else False
            if is_danger:
                st.markdown(f"🔴 **{zone}** (Active Alert)")
            else:
                st.markdown(f"🟡 {zone}")

    st.divider()
    col_info, col_contact = st.columns(2)
    with col_info:
        with st.expander("📢 Emergency Do's and Don'ts", expanded=True):
            st.write("✅ **DO:** Move to higher ground immediately.")
            st.write("✅ **DO:** Turn off all electrical utilities.")
            st.write("❌ **DON'T:** Walk or drive through flood waters.")
            st.write("❌ **DON'T:** Touch electrical equipment if you are wet.")

    with col_contact:
        with st.expander("☎️ Emergency Contacts", expanded=True):
            st.error("📞 **Disaster Management:** 108")
            st.error("📞 **Flood Helpline:** 1912")
            st.write("🏢 **GHMC Control Room:** 040-2345-XXXX")