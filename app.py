import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time
import plotly.express as px

# Page Configuration for Mobile Responsiveness
st.set_page_config(
    page_title="Kratu Hall Mess Portal",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Fetch Variables from Secrets
WEBAPP_URL = st.secrets["WEBAPP_URL"]
SHEET_CSV_URL = st.secrets["SHEET_CSV_URL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

tab1, tab2 = st.tabs(["📝 Student Feedback Form", "📊 Admin Dashboard"])

# ==========================================
# PART 1: STUDENT FACING FEEDBACK FORM
# ==========================================
with tab1:
    st.title("Kratu Hall Catering Feedback")
    st.markdown("Your ratings directly enforce vendor compliance under official Annexure-14 guidelines.")
    
    with st.form("feedback_form", clear_on_submit=True):
        st.subheader("1. Identification")
        room_number = st.text_input("Room Number", placeholder="Enter your room number (e.g., 101-K)")
        
        st.subheader("2. Evaluation Metrics (Annexure-14)")
        q1 = st.slider("Food Quality, Quantity, and Taste (Max: 40)", 0, 40, 25, 1)
        q2 = st.slider("Hygiene and Sanitation (Max: 30)", 0, 30, 20, 1)
        q3 = st.slider("Service Quality (Max: 20)", 0, 20, 15, 1)
        q4 = st.slider("Student Satisfaction (Max: 10)", 0, 10, 7, 1)
        
        submitted = st.form_submit_button("Submit Anonymous Ratings", use_container_width=True)
        
        if submitted:
            if not room_number.strip():
                st.error("Submission failed: Room Number is required.")
            else:
                total_score = q1 + q2 + q3 + q4
                payload = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": room_number.strip().upper(),
                    "food": q1,
                    "hygiene": q2,
                    "service": q3,
                    "satisfaction": q4,
                    "total": total_score
                }
                
                try:
                    # Send data securely to Google Apps Script
                    response = requests.post(WEBAPP_URL, json=payload)
                    if response.status_code == 200 and response.json().get("status") == "success":
                        st.success("Success! Your ratings have been recorded securely.")
                    else:
                        st.error("Submission failed on the server side.")
                except Exception as e:
                    st.error(f"Network error. Details: {e}")

# ==========================================
# PART 2: ADMIN FACING DASHBOARD
# ==========================================
with tab2:
    st.title("Administrative Performance Panel")
    
    password_input = st.text_input("Enter Admin Password to Unlock", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("Access Granted.")
        
        try:
            # Bypass Google cache for real-time data updates
            cache_busting_url = f"{SHEET_CSV_URL}&t={int(time.time())}"
            df = pd.read_csv(cache_busting_url)
            
            if df.empty or len(df) == 0:
                st.warning("Database is empty. Waiting for student submissions.")
            else:
                numeric_cols = ["Food Quality", "Hygiene", "Service Quality", "Satisfaction", "Total Score"]
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.dropna(subset=["Total Score"])
                total_responses = len(df)
                avg_total = df["Total Score"].mean()
                student_weighted_score = (avg_total / 100) * 50
                
                st.markdown("### Executive Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Ballots Cast", f"{total_responses}")
                col2.metric("Raw Score Avg", f"{avg_total:.2f} / 100")
                col3.metric("Final Weighted Score", f"{student_weighted_score:.2f} / 50")
                
                st.markdown("---")
                st.markdown("### Chronological Performance Trajectory")
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df_sorted = df.sort_values(by='Timestamp')
                df_sorted['Date'] = df_sorted['Timestamp'].dt.date
                daily_trend = df_sorted.groupby('Date')['Total Score'].mean().reset_index()
                
                fig_trend = px.line(
                    daily_trend, x='Date', y='Total Score',
                    title='Daily Aggregated Score Trend (Passing: >70)',
                    markers=True
                )
                fig_trend.add_hline(y=70, line_dash="dash", line_color="red")
                st.plotly_chart(fig_trend, use_container_width=True)
                
                st.markdown("### Verified Data Audit Log")
                st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Export Raw Evidence CSV",
                    data=csv,
                    file_name=f"Kratu_Mess_Report_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Failed to load data. Error: {e}")
            
    elif password_input:
        st.error("Invalid Administrative Credentials. Access Denied.")
