import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import time
import plotly.express as px

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Kratu Hall ERP", 
    page_icon="🏛️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Modern UI Custom CSS ---
st.markdown("""
<style>
    /* Hide the default Streamlit top menu and footer for a clean app look */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style the Forms to look like floating modern cards */
    [data-testid="stForm"] {
        background-color: #ffffff;
        border-radius: 20px;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid #f0f2f6;
        padding: 25px;
    }
    
    /* Style the Submit Buttons with a modern gradient and hover animation */
    [data-testid="baseButton-secondaryFormSubmit"] {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border-radius: 30px;
        border: none;
        box-shadow: 0px 4px 10px rgba(76, 175, 80, 0.3);
        font-weight: bold;
        transition: all 0.3s ease;
    }
    [data-testid="baseButton-secondaryFormSubmit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0px 6px 15px rgba(76, 175, 80, 0.5);
        color: white;
    }
    
    /* Improve the styling of Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        background-color: #f8f9fa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e8f5e9;
        color: #2E7D32 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Hero Banner Image ---
st.image("https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=1200&q=80", use_container_width=True)

# --- 4. Fetch Variables from Secrets ---
WEBAPP_URL = st.secrets["WEBAPP_URL"]
SHEET_CSV_URL = st.secrets["SHEET_CSV_URL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- 5. Main App Navigation ---
st.title("Kratu Hall Digital Portal")
tab1, tab2, tab3, tab4 = st.tabs(["📝 Ratings", "📅 Leave Rebate", "🍲 Menu Poll", "📊 Admin"])

# ==========================================
# TAB 1: RATINGS 
# ==========================================
with tab1:
    st.subheader("Daily Catering Evaluation")
    st.markdown("Rate the mess based strictly on Annexure-14 guidelines.")
    
    with st.form("feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        room_number = col1.text_input("Room Number", placeholder="e.g., 101-K")
        student_name = col2.text_input("Name", placeholder="Enter your name")
        
        st.markdown("---")
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
                    "action": "rating", 
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": room_number.upper(), "name": student_name.title(),
                    "food": q1, "hygiene": q2, "service": q3, "satisfaction": q4,
                    "total": q1+q2+q3+q4, "comments": comments
                }
                try:
                    requests.post(WEBAPP_URL, json=payload)
                    st.success("Rating submitted successfully.")
                except Exception as e:
                    st.error(f"Network error. Details: {e}")

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
        
        delta = end_date - start_date
        leave_days = delta.days
        
        if st.form_submit_button("Apply for Rebate", use_container_width=True):
            if not l_room or not l_name:
                st.error("Identification required.")
            elif leave_days < 5:
                st.error(f"Application Denied: Your leave is {leave_days} days. Rules require a minimum of 5 continuous days for a rebate.")
            else:
                payload = {
                    "action": "leave", 
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": l_room.upper(), "name": l_name.title(),
                    "start_date": str(start_date), "end_date": str(end_date),
                    "days": leave_days, "reason": reason
                }
                try:
                    requests.post(WEBAPP_URL, json=payload)
                    st.success(f"Approved! {leave_days} days of rebate logged for processing.")
                except Exception as e:
                    st.error(f"Network error: {e}")

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
                    "action": "poll", 
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": p_room.upper(), "name": p_name.title(), "vote": vote
                }
                try:
                    requests.post(WEBAPP_URL, json=payload)
                    st.success("Your vote has been counted!")
                except Exception as e:
                    st.error(f"Network error: {e}")

# ==========================================
# TAB 4: ADMIN DASHBOARD
# ==========================================
with tab4:
    st.subheader("Administrative Performance Panel")
    
    password_input = st.text_input("Enter Admin Password to Unlock", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("Access Granted.")
        
        try:
            cache_busting_url = f"{SHEET_CSV_URL}&t={int(time.time())}"
            df = pd.read_csv(cache_busting_url)
            
            if df.empty or len(df) == 0:
                st.warning("Database is empty. Waiting for student submissions.")
            else:
                numeric_cols = ["Food Quality", "Hygiene", "Service Quality", "Satisfaction", "Total Score"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if "Total Score" in df.columns:
                    df_scores = df.dropna(subset=["Total Score"])
                    
                    if not df_scores.empty:
                        total_responses = len(df_scores)
                        avg_total = df_scores["Total Score"].mean()
                        student_weighted_score = (avg_total / 100) * 50
                        
                        st.markdown("### Executive Summary")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Ballots Cast", f"{total_responses}")
                        col2.metric("Raw Score Avg", f"{avg_total:.2f} / 100")
                        col3.metric("Final Weighted Score", f"{student_weighted_score:.2f} / 50")
                        
                        st.markdown("---")
                        st.markdown("### Chronological Performance Trajectory")
                        df_scores['Timestamp'] = pd.to_datetime(df_scores['Timestamp'])
                        df_sorted = df_scores.sort_values(by='Timestamp')
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
