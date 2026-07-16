import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date, timedelta
import time
import plotly.express as px

st.set_page_config(page_title="Kratu Hall ERP", page_icon="🏛️", layout="centered")

# --- Custom CSS & Banner ---
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    [data-testid="stForm"] {
        background-color: #ffffff; border-radius: 15px;
        box-shadow: 0px 8px 20px rgba(0,0,0,0.08); border: 1px solid #f0f2f6;
        padding: 25px; margin-bottom: 20px;
    }
    [data-testid="stForm"] button {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%) !important;
        color: white !important; border-radius: 30px !important; border: none !important;
        box-shadow: 0px 4px 10px rgba(76,175,80,0.3) !important; font-weight: bold !important;
        padding: 10px 20px !important; transition: all 0.3s ease !important;
    }
    [data-testid="stForm"] button:hover { transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

st.markdown("""<img src="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=1200&q=80" style="width: 100%; height: 180px; object-fit: cover; border-radius: 15px; margin-bottom: 20px;">""", unsafe_allow_html=True)

# --- Fetch Secrets ---
WEBAPP_URL = st.secrets["WEBAPP_URL"]
SHEET_CSV_URL = st.secrets["SHEET_CSV_URL"]
CONFIG_CSV_URL = st.secrets["CONFIG_CSV_URL"]
STUDENT_DB_CSV_URL = st.secrets["STUDENT_DB_CSV_URL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- Fetch Dynamic Menu & Student DB ---
try:
    df_config = pd.read_csv(f"{CONFIG_CSV_URL}&t={int(time.time())}")
    dynamic_menu = df_config['Menu Items'].dropna().tolist()
except:
    dynamic_menu = ["Menu loading... (Admin must set menu)"]

try:
    # This reads your new database tab!
    df_students = pd.read_csv(f"{STUDENT_DB_CSV_URL}&t={int(time.time())}")
    # This combines the Room Number and Name into one clean dropdown option
    df_students['Identity'] = df_students['Room No'].astype(str) + " - " + df_students['Name']
    student_identities = ["Select your Room & Name..."] + df_students['Identity'].tolist()
except:
    student_identities = ["Database loading error. Please refresh."]

# --- Navigation ---
st.title("Kratu Hall Digital Portal")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Ratings", "🔄 Diet Switch", "📅 Rebate", "🍲 Poll", "📊 Admin"])

# ==========================================
# TAB 1: RATINGS (Smart Dropdown Integrated)
# ==========================================
with tab1:
    st.markdown("### Daily Catering Evaluation")
    st.info(f"**Today's Highlight Menu:** {', '.join(dynamic_menu[:3])}...") 
    
    with st.form("feedback_form", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        meal_date = col_m1.date_input("Meal Date", max_value=date.today())
        meal_type = col_m2.selectbox("Meal Type", ["Breakfast", "Lunch", "Snacks", "Dinner"])
        
        # SMART DROPDOWN
        identity = st.selectbox("Who are you? (Room - Name)*", student_identities)
        reg_no = st.text_input("Registration Number* (Acts as your signature)", placeholder="e.g., 230203...")
        
        st.markdown("---")
        q1 = st.slider("Food Quality & Taste (Max: 40)", 0, 40, 25)
        q2 = st.slider("Hygiene & Sanitation (Max: 30)", 0, 30, 20)
        q3 = st.slider("Service Quality (Max: 20)", 0, 20, 15)
        q4 = st.slider("Student Satisfaction (Max: 10)", 0, 10, 7)
        comments = st.text_area("General Feedback or Specific Issues (Optional)")
        
        if st.form_submit_button("Submit Rating", use_container_width=True):
            if identity.startswith("Select") or not reg_no:
                st.error("Please select your identity and provide your Registration Number.")
            else:
                # The code splits your smart dropdown back into separate columns for Google Sheets!
                room_number = identity.split(" - ")[0]
                student_name = identity.split(" - ")[1]
                
                payload = {
                    "action": "rating", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "meal_date": str(meal_date), "meal_type": meal_type,
                    "reg": reg_no, "room": room_number.upper(), "name": student_name.title(),
                    "food": q1, "hygiene": q2, "service": q3, "satisfaction": q4,
                    "total": q1+q2+q3+q4, "comments": comments
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("Rating submitted securely.")

# ==========================================
# TAB 2: DIET SWITCH 
# ==========================================
with tab2:
    st.markdown("### 🔄 Daily Diet Override")
    st.info("Switch your diet temporarily for tomorrow. **Deadline: 10:00 PM nightly.**")
    
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    tomorrow_date = ist_now.date() + timedelta(days=1)
    is_past_deadline = ist_now.hour >= 22
    
    if is_past_deadline:
        st.error(f"The 10:00 PM deadline has passed. You cannot change your preference for {tomorrow_date}.")
    else:
        st.success(f"Open: You are selecting your preference for tomorrow ({tomorrow_date}).")
        with st.form("switch_form", clear_on_submit=True):
            identity_s = st.selectbox("Who are you? (Room - Name)*", student_identities)
            new_diet = st.radio("Tomorrow's Preference:", ["Vegetarian", "Non-Vegetarian"])
            
            if st.form_submit_button("Lock in Preference", use_container_width=True):
                if identity_s.startswith("Select"):
                    st.error("Please select your identity.")
                else:
                    room_s = identity_s.split(" - ")[0]
                    name_s = identity_s.split(" - ")[1]
                    payload = {
                        "action": "switch", "timestamp": ist_now.strftime("%Y-%m-%d %H:%M:%S"),
                        "target_date": str(tomorrow_date), "room": room_s.upper(),
                        "name": name_s.title(), "diet": new_diet
                    }
                    requests.post(WEBAPP_URL, json=payload)
                    st.success(f"Success! Your diet for {tomorrow_date} is logged as {new_diet}.")

# ==========================================
# TAB 3: LEAVE & REBATE
# ==========================================
with tab3:
    st.markdown("### Official Mess Rebate Application")
    with st.form("leave_form", clear_on_submit=True):
        identity_l = st.selectbox("Who are you? (Room - Name)*", student_identities)
        l_reg = st.text_input("Registration Number*")
        
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Departure Date", min_value=date.today())
        end_date = col2.date_input("Return Date", min_value=date.today())
        
        reason = st.text_input("Reason & Approving Authority (e.g., Medical - HoD)")
        proof_link = st.text_input("Link to Proof (Paste Google Drive/Photo link here)")
        
        leave_days = (end_date - start_date).days
        
        if st.form_submit_button("Apply for Rebate", use_container_width=True):
            if leave_days < 5:
                st.error(f"Denied: Your leave is {leave_days} days. Rules require a minimum of 5.")
            elif identity_l.startswith("Select") or not l_reg:
                st.error("Identity and Registration Number are required.")
            else:
                room_l = identity_l.split(" - ")[0]
                name_l = identity_l.split(" - ")[1]
                payload = {
                    "action": "leave", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reg": l_reg, "room": room_l.upper(), "name": name_l.title(),
                    "start_date": str(start_date), "end_date": str(end_date),
                    "days": leave_days, "reason": reason, "link": proof_link
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("Rebate logged for processing.")

# ==========================================
# TAB 4: MENU POLL 
# ==========================================
with tab4:
    st.markdown("### Weekly Menu Poll")
    with st.form("poll_form", clear_on_submit=True):
        identity_p = st.selectbox("Who are you? (Room - Name)*", student_identities)
        vote = st.radio("Select your preference:", dynamic_menu)
        
        if st.form_submit_button("Cast Vote", use_container_width=True):
            if identity_p.startswith("Select"):
                st.error("Please select your identity.")
            else:
                room_p = identity_p.split(" - ")[0]
                name_p = identity_p.split(" - ")[1]
                payload = {
                    "action": "poll", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "room": room_p.upper(), "name": name_p.title(), "vote": vote
                }
                requests.post(WEBAPP_URL, json=payload)
                st.success("Your vote has been counted!")

# ==========================================
# TAB 5: ADMIN DASHBOARD 
# ==========================================
with tab5:
    password_input = st.text_input("Enter Admin Password to Unlock", type="password")
    
    if password_input == ADMIN_PASSWORD:
        st.success("Access Granted.")
        
        # --- CMS Control Panel ---
        st.markdown("#### ⚙️ Control Panel: Update Menu")
        with st.form("update_menu_form"):
            new_menu_string = st.text_input("Enter new options (separated by commas):", value=", ".join(dynamic_menu))
            if st.form_submit_button("Publish New Menu", use_container_width=True):
                menu_list = [item.strip() for item in new_menu_string.split(',')]
                requests.post(WEBAPP_URL, json={"action": "update_menu", "menu_items": menu_list})
                st.success("Menu updated! Refresh the page to see changes.")
        
        st.markdown("---")
        
        # --- Analytics ---
        try:
            df = pd.read_csv(f"{SHEET_CSV_URL}&t={int(time.time())}")
            df = df.dropna(subset=["Total Score"])
            student_weighted_score = (df["Total Score"].mean() / 100) * 50
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Ballots", f"{len(df)}")
            col2.metric("Raw Avg", f"{df['Total Score'].mean():.2f}")
            col3.metric("Weighted", f"{student_weighted_score:.2f} / 50")
            
            df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
            fig = px.line(df.groupby('Date')['Total Score'].mean().reset_index(), x='Date', y='Total Score', title='Trend')
            fig.add_hline(y=70, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
        except Exception:
            st.warning("Database empty or loading.")
