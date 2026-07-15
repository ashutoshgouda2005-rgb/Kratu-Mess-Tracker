import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import time
import plotly.express as px

# --- Config & Secrets ---
st.set_page_config(page_title="Kratu Hall ERP", page_icon="🏛️", layout="centered")
WEBAPP_URL = st.secrets["WEBAPP_URL"]
SHEET_CSV_URL = st.secrets["SHEET_CSV_URL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- Main App Navigation ---
st.title("Kratu Hall Digital Portal")
tab1, tab2, tab3, tab4 = st.tabs(["📝 Ratings", "📅 Leave Rebate", "🍲 Menu Poll", "📊 Admin"])

# ==========================================
# TAB 1: RATINGS (Updated with Action Tag)
# ==========================================
with tab1:
    st.subheader("Daily Catering Evaluation")
    with st.form("feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        room_number = col1.text_input("Room Number", placeholder="e.g., 101-K")
        student_name = col2.text_input("Name", placeholder="Enter your name")
        
        q1 = st.slider("Food Quality & Taste (Max: 40)", 0, 40, 25)
        q2 = st.slider("Hygiene & Sanitation (Max: 30)", 0, 30, 20)
        q3 = st.slider("Service Quality (Max: 20)", 0, 20, 15)
        q4 = st.slider("Student Satisfaction (Max: 10)", 0, 10, 7)
        comments = st.text_area("Specific Issues? (Optional)")
        
        if st.form_submit_button("Submit Rating", use_container_width=True):
            if not room_number or not student_name:
                st.error("Room Number and Name are required.")
            else:
                payload = {
                    "action": "rating", # Tells the script to send to Sheet1
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": room_number.upper(), "name": student_name.title(),
                    "food": q1, "hygiene": q2, "service": q3, "satisfaction": q4,
                    "total": q1+q2+q3+q4, "comments": comments
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("Rating submitted successfully.")

# ==========================================
# TAB 2: LEAVE & REBATE CALCULATOR
# ==========================================
with tab2:
    st.subheader("Official Mess Rebate Application")
    st.info("Rule: You must apply 3 days prior, and the leave must be a continuous period of 5+ days.")
    
    with st.form("leave_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        l_room = col1.text_input("Room No.")
        l_name = col2.text_input("Full Name")
        
        start_date = st.date_input("Departure Date", min_value=date.today())
        end_date = st.date_input("Return Date", min_value=date.today())
        reason = st.text_input("Reason & Approving Authority (e.g., Medical - HoD Approved)")
        
        # Calculate days
        delta = end_date - start_date
        leave_days = delta.days
        
        if st.form_submit_button("Apply for Rebate", use_container_width=True):
            if not l_room or not l_name:
                st.error("Identification required.")
            elif leave_days < 5:
                st.error(f"Application Denied: Your leave is {leave_days} days. Rules require a minimum of 5 continuous days for a rebate.")
            else:
                payload = {
                    "action": "leave", # Tells the script to send to Leaves tab
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": l_room.upper(), "name": l_name.title(),
                    "start_date": str(start_date), "end_date": str(end_date),
                    "days": leave_days, "reason": reason
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success(f"Approved! {leave_days} days of rebate logged for processing.")

# ==========================================
# TAB 3: MENU POLL
# ==========================================
with tab3:
    st.subheader("Weekly Sunday Special Poll")
    st.markdown("Vote for next week's special dinner item. The majority wins.")
    
    with st.form("poll_form", clear_on_submit=True):
        p_room = st.text_input("Room No.")
        p_name = st.text_input("Name")
        vote = st.radio("Select your preference:", ["Chicken Biryani", "Mutton Curry", "Paneer Butter Masala", "Mushroom Do Pyaza"])
        
        if st.form_submit_button("Cast Vote", use_container_width=True):
            if not p_room or not p_name:
                st.error("Identification required.")
            else:
                payload = {
                    "action": "poll", # Tells the script to send to Polls tab
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": p_room.upper(), "name": p_name.title(), "vote": vote
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("Your vote has been counted!")

# ==========================================
# TAB 4: ADMIN DASHBOARD (Unchanged Logic)
# ==========================================
with tab4:
    if st.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
        st.success("Access Granted.")
        try:
            df = pd.read_csv(f"{SHEET_CSV_URL}&t={int(time.time())}")
            df = df.dropna(subset=["Total Score"])
            
            st.metric("Final Weighted Score", f"{(df['Total Score'].mean() / 100) * 50:.2f} / 50")
            
            df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
            fig = px.line(df.groupby('Date')['Total Score'].mean().reset_index(), x='Date', y='Total Score', title='Trend')
            fig.add_hline(y=70, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
        except:
            st.warning("Waiting for data.")
