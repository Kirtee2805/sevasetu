"""
SevaSetu — app.py
AI Powered Public Healthcare Supply Chain Intelligence Dashboard.

Premium Streamlit dashboard modularized into components and pages.
"""
import firebase_admin

from friebase_admin import credentials
from firebase_admin import auth

cred = credentials.certificate('firebase_credential.json')
firebase_admin.initialize_app(cred)

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import random
import time

# --- DATA FETCHING (ADD THIS AFTER IMPORTS) ---
@st.cache_data(ttl=60)
def get_dashboard_data():
    try:
        # Replace with your actual API endpoint
        response = requests.get(f"{API_URL}/api/dashboard")
        return response.json().get("data", {}) if response.status_code == 200 else {}
    except:
        return {}

# ==========================================
# CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="SevaSetu",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOAD CSS
# ==========================================

css_file = Path(__file__).parent / "assets" / "style.css"

if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text()}</style>",
        unsafe_allow_html=True
    )

# ==========================================
# SAMPLE DATA
# Replace later using FastAPI
# ==========================================

districts = [
    "Ahmedabad", "Rajkot", "Surat", 
    "Vadodara", "Bhavnagar", "Jamnagar"
]

summary = {
    "patients": 25431,
    "stock_alerts": 43,
    "critical": 11,
    "trust": 92,
    "beds": 87,
    "doctors": 95,
    "outbreaks": 2
}

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown("# 🏥 SevaSetu")
    st.caption("Healthcare Intelligence Platform")
    st.divider()

    page = st.radio(
        "",
        [
            "🏠 Overview",
            "💊 Medicine Alerts",
            "👥 Patient Footfall",
            "👨‍⚕ Doctor Attendance",
            "🛏 Bed Availability",
            "🦠 Outbreak Detection",
            "🛡 Trust Score",
            "📊 Analytics",
            "🏥 PHC Data Entry",
            "⚙ Pipeline Status"
        ]
    )

    st.divider()
    st.success("🟢 FastAPI Connected")
    st.success("🟢 Google Firebase")
    st.success("🟢 AI Models Ready")
    st.success("🟢 Dashboard Online")
    
    st.divider()
    st.markdown("### 👤 User")
    st.write("District Officer")
    st.caption("Government of Gujarat")
    
    st.divider()
    st.markdown("### 🚀 Google Build with AI")
    st.caption("Team Alt_26")

# ==========================================
# NAVBAR
# ==========================================

col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

with col1:
    st.title("🏥 SevaSetu")
    st.caption("AI Powered Healthcare Supply Chain Intelligence Platform")

with col2:
    st.metric("Pipeline", "Running")

with col3:
    st.metric("Updated", datetime.now().strftime("%H:%M"))

with col4:
    st.metric("District", "Rajkot")

st.divider()

# ==========================================
# KPI CARD FUNCTION
# ==========================================

def card(title, value, delta, emoji):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{emoji} {title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 🏠 OVERVIEW PAGE
# ==========================================

if page == "🏠 Overview":
    st.header("Healthcare Overview")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Today's Patients", summary["patients"], "+12%", "👥")
    with c2:
        card("Medicine Alerts", summary["stock_alerts"], "43 Active", "💊")
    with c3:
        card("Trust Score", f'{summary["trust"]}%', "+2%", "🛡")
    with c4:
        card("Outbreaks", summary["outbreaks"], "Live", "🦠")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([2, 1])
    
    with left:
        df = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Patients": [3500, 3700, 3900, 4200, 4100, 4700, 4800]
        })
        fig = px.line(
            df, x="Day", y="Patients", markers=True, title="Weekly Patient Footfall"
        )
        fig.update_layout(height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
    with right:
        pie = px.pie(
            values=[43, 28, 17, 12],
            names=["Critical", "High", "Medium", "Low"],
            title="Medicine Risk"
        )
        pie.update_layout(height=420, template="plotly_white")
        st.plotly_chart(pie, use_container_width=True)

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 District Wise Patient Comparison")
        district_df = pd.DataFrame({
            "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
            "Patients": [5200, 4100, 4800, 3500, 2700, 2200]
        })
        fig = px.bar(
            district_df, x="District", y="Patients", color="Patients", 
            color_continuous_scale="Blues"
        )
        fig.update_layout(
            template="plotly_white", height=420, title="Patients by District", coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("🚨 Critical Alerts")
        alerts = pd.DataFrame({
            "Medicine": ["Paracetamol", "ORS", "IFA Tablets", "Amoxicillin", "Insulin"],
            "District": ["Rajkot", "Ahmedabad", "Surat", "Vadodara", "Bhavnagar"],
            "Risk": ["Critical", "High", "Critical", "Medium", "High"]
        })
        st.dataframe(alerts, use_container_width=True, hide_index=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏥 PHC Performance")
        phc = pd.DataFrame({
            "PHC": ["PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05"],
            "Trust": [95, 90, 84, 88, 97]
        })
        fig = px.bar(phc, x="PHC", y="Trust", color="Trust", color_continuous_scale="Greens")
        fig.update_layout(template="plotly_white", height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("🦠 Disease Distribution")
        disease = pd.DataFrame({
            "Disease": ["Fever", "Diabetes", "TB", "Hypertension", "Others"],
            "Cases": [350, 180, 75, 210, 120]
        })
        fig = px.pie(disease, names="Disease", values="Cases", hole=.55)
        fig.update_layout(template="plotly_white", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Live Healthcare Records")
    
    live = pd.DataFrame({
        "District": ["Rajkot", "Ahmedabad", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Patients": [421, 502, 478, 355, 244, 187],
        "Doctors": [14, 18, 17, 12, 9, 8],
        "Beds": [78, 94, 83, 61, 55, 48],
        "Trust": [95, 91, 89, 88, 85, 82],
        "Status": ["Normal", "Normal", "Alert", "Normal", "Critical", "Normal"]
    })

    def color_status(val):
        if val == "Critical":
            return "background-color:#FEE2E2;color:red;font-weight:bold"
        elif val == "Alert":
            return "background-color:#FEF3C7;color:#B45309;font-weight:bold"
        else:
            return "background-color:#DCFCE7;color:green;font-weight:bold"

    st.dataframe(
        live.style.map(color_status, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("")
    st.success("✅ AI Pipeline Running Successfully")
    st.info("📡 Last Updated : " + datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    st.caption("Google Build with AI • Team Alt_26 • SevaSetu")

# ==========================================
# 💊 MEDICINE ALERTS PAGE
# ==========================================

elif page == "💊 Medicine Alerts":
    st.header("💊 Medicine Stock Intelligence")
    st.caption("Real-time monitoring of medicine stock, shortages and AI predictions")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"])
    with f2:
        medicine = st.selectbox("Medicine", ["All", "Paracetamol", "ORS", "IFA Tablets", "Amoxicillin", "Insulin"])
    with f3:
        risk = st.selectbox("Risk Level", ["All", "Critical", "High", "Medium", "Low"])
    with f4:
        st.date_input("Report Date")

    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Critical Stockouts", "11", "+3 Today", "🚨")
    with c2:
        card("High Risk Medicines", "28", "+5", "⚠️")
    with c3:
        card("Average Stock Coverage", "19 Days", "-2 Days", "📦")
    with c4:
        card("AI Prediction Accuracy", "96%", "+1.5%", "🤖")

    st.markdown("")

    left, right = st.columns([2, 1])
    with left:
        stock_df = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Critical": [8, 9, 11, 13, 10, 12, 11],
            "High": [18, 20, 19, 21, 24, 25, 28]
        })
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_df["Day"], y=stock_df["Critical"], mode="lines+markers", name="Critical"))
        fig.add_trace(go.Scatter(x=stock_df["Day"], y=stock_df["High"], mode="lines+markers", name="High"))
        fig.update_layout(title="Medicine Stock Alert Trend", template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        risk_df = pd.DataFrame({
            "Risk": ["Critical", "High", "Medium", "Low"],
            "Count": [11, 28, 34, 58]
        })
        fig = px.pie(
            risk_df, names="Risk", values="Count", hole=.60, color="Risk",
            color_discrete_map={"Critical": "red", "High": "orange", "Medium": "gold", "Low": "green"}
        )
        fig.update_layout(title="Risk Distribution", template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District-wise Stock Availability")
    
    district_stock = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Stock %": [96, 83, 91, 74, 67, 88]
    })
    fig = px.bar(district_stock, x="District", y="Stock %", color="Stock %", color_continuous_scale="RdYlGn")
    fig.update_layout(template="plotly_white", height=430, coloraxis_showscale=False, title="Current Medicine Availability")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 Top Critical Medicines")
    top = pd.DataFrame({
        "Medicine": ["Paracetamol", "ORS", "IFA Tablets", "Amoxicillin", "Insulin"],
        "District": ["Rajkot", "Bhavnagar", "Ahmedabad", "Surat", "Vadodara"],
        "Remaining Days": [2, 3, 4, 5, 6],
        "Probability": [98, 95, 93, 89, 86]
    })
    st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📦 AI Stock-out Predictions")
    prediction_df = pd.DataFrame({
        "District": ["Rajkot", "Ahmedabad", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Medicine": ["Paracetamol", "ORS", "IFA Tablets", "Amoxicillin", "Insulin", "Vitamin A"],
        "Current Stock": [120, 90, 45, 68, 40, 180],
        "Daily Consumption": [38, 27, 20, 16, 11, 14],
        "Days Remaining": [3, 4, 2, 5, 3, 12],
        "Probability (%)": [98, 94, 99, 87, 92, 25],
        "Risk": ["Critical", "Critical", "Critical", "High", "High", "Low"]
    })

    def risk_color(value):
        if value == "Critical":
            return "background-color:#FEE2E2;color:#B91C1C;font-weight:bold"
        elif value == "High":
            return "background-color:#FEF3C7;color:#B45309;font-weight:bold"
        elif value == "Medium":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        return "background-color:#DCFCE7;color:#15803D;font-weight:bold"

    st.dataframe(
        prediction_df.style.map(risk_color, subset=["Risk"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("🤖 AI Recommendations")
    
    rec1, rec2 = st.columns(2)
    with rec1:
        st.success("### ✅ Recommendation 1\nIncrease **Paracetamol** supply to **Rajkot PHCs**\nExpected shortage within **3 days**\nPriority : **Very High**")
        st.warning("### ⚠ Recommendation 2\nMove **500 ORS packets**\nAhmedabad ➜ Bhavnagar\nto avoid stock-out.")
        st.info("### 📈 Recommendation 3\nTrust score decreasing in **Bhavnagar**\nRecommend field verification.")
    with rec2:
        st.error("### 🚨 Emergency Action\nIFA Tablets\nCritical shortage\nSurat District\nImmediate procurement required.")
        st.success("### 🚑 Redistribution\nMove surplus stock\nJamnagar ➜ Rajkot")
        st.info("### 🤖 AI Confidence\nPrediction Accuracy\n96.4%")

    st.markdown("---")
    st.subheader("🚨 Live Alert Feed")
    alerts = [
        "🔴 Rajkot : Paracetamol will finish in 3 days",
        "🔴 Ahmedabad : ORS shortage predicted",
        "🟠 Surat : IFA Tablets demand increasing",
        "🟢 Jamnagar : Stock levels healthy",
        "🟠 Vadodara : Emergency medicine consumption high",
        "🟢 Bhavnagar : Procurement completed"
    ]
    for item in alerts:
        st.info(item)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("📥 Download CSV", prediction_df.to_csv(index=False), "medicine_alerts.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.button("📄 Generate PDF Report", use_container_width=True)
    with c3:
        st.button("📧 Send Alert to PHC", use_container_width=True)

    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Prediction Model", "Online", "✓")
    with s2:
        st.metric("FastAPI", "Connected", "✓")
    with s3:
        st.metric("Firebase", "Connected", "✓")
    with s4:
        st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

    st.success("✅ Medicine Intelligence Module Running Successfully")

# ==========================================
# 👥 PATIENT FOOTFALL PAGE
# ==========================================

elif page == "👥 Patient Footfall":
    st.header("👥 Patient Footfall Analytics")
    st.caption("AI-powered OPD monitoring across Gujarat PHCs")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="pf_district")
    with f2:
        phc = st.selectbox("PHC", ["All PHCs", "PHC-01", "PHC-02", "PHC-03", "PHC-04"], key="pf_phc")
    with f3:
        duration = st.selectbox("Duration", ["Today", "Last 7 Days", "Last Month", "Last Year"], key="pf_duration")
    with f4:
        st.date_input("Date", key="pf_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Today's Patients", "25,431", "+12%", "👥")
    with c2:
        card("Monthly Patients", "6,78,245", "+6%", "📅")
    with c3:
        card("Average OPD", "312", "+18", "🏥")
    with c4:
        card("Emergency", "54", "-4", "🚑")

    st.markdown("")

    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Patients": [350, 420, 480, 520, 560, 610, 590]
        })
        fig = px.area(trend, x="Day", y="Patients", markers=True, color_discrete_sequence=["#2563EB"])
        fig.update_layout(template="plotly_white", height=420, title="Daily OPD Trend")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        gender = pd.DataFrame({
            "Category": ["Male", "Female", "Children"],
            "Count": [11800, 11120, 2511]
        })
        fig = px.pie(gender, names="Category", values="Count", hole=.55)
        fig.update_layout(template="plotly_white", height=420, title="Patient Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District Comparison")
    
    district_data = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Patients": [5200, 4100, 4850, 3560, 2890, 2210]
    })
    fig = px.bar(district_data, x="District", y="Patients", color="Patients", color_continuous_scale="Blues")
    fig.update_layout(template="plotly_white", height=430, coloraxis_showscale=False, title="District Wise OPD")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        hourly = pd.DataFrame({
            "Hour": ["8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM"],
            "Patients": [22, 51, 78, 95, 110, 92, 71, 53, 34]
        })
        fig = px.line(hourly, x="Hour", y="Patients", markers=True)
        fig.update_layout(template="plotly_white", height=380, title="Hourly Patient Footfall")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        age = pd.DataFrame({
            "Age Group": ["0-18", "19-35", "36-50", "51-65", "65+"],
            "Patients": [210, 520, 410, 285, 130]
        })
        fig = px.bar(age, x="Age Group", y="Patients", color="Patients", color_continuous_scale="Teal")
        fig.update_layout(template="plotly_white", height=380, coloraxis_showscale=False, title="Age-wise Patients")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🦠 Disease Distribution")
    
    d1, d2 = st.columns([2, 1])
    with d1:
        disease_df = pd.DataFrame({
            "Disease": ["Fever", "Diabetes", "Hypertension", "TB", "Asthma", "Others"],
            "Patients": [520, 280, 240, 85, 120, 175]
        })
        fig = px.bar(disease_df, x="Disease", y="Patients", color="Patients", color_continuous_scale="Viridis")
        fig.update_layout(template="plotly_white", height=420, coloraxis_showscale=False, title="Most Common Diseases")
        st.plotly_chart(fig, use_container_width=True)

    with d2:
        disease_pie = px.pie(disease_df, names="Disease", values="Patients", hole=.55)
        disease_pie.update_layout(template="plotly_white", height=420, title="Disease Share")
        st.plotly_chart(disease_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("🏥 PHC OPD Performance")
    
    opd_df = pd.DataFrame({
        "PHC": ["PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05", "PHC-06"],
        "OPD": [310, 425, 280, 395, 365, 450]
    })
    fig = px.bar(opd_df, x="PHC", y="OPD", color="OPD", color_continuous_scale="Blues")
    fig.update_layout(template="plotly_white", height=420, title="Today's OPD Performance", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Live Patient Records")
    
    patient_df = pd.DataFrame({
        "District": ["Rajkot", "Ahmedabad", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Today's Patients": [421, 518, 478, 355, 240, 198],
        "Emergency": [18, 26, 21, 14, 9, 6],
        "Doctors": [14, 19, 17, 13, 10, 8],
        "Average Wait": ["12 min", "16 min", "14 min", "10 min", "9 min", "7 min"],
        "Status": ["Normal", "Busy", "Normal", "Busy", "Normal", "Normal"]
    })

    def highlight_status(val):
        if val == "Busy":
            return "background-color:#FEF3C7;color:#B45309;font-weight:bold"
        return "background-color:#DCFCE7;color:#15803D;font-weight:bold"

    st.dataframe(
        patient_df.style.map(highlight_status, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("🤖 AI Insights")
    
    i1, i2 = st.columns(2)
    with i1:
        st.success("### 📈 Patient Growth\n• OPD increased **12%** today\n• Highest footfall: **Ahmedabad**\n• Lowest footfall: **Jamnagar**")
        st.info("### 🧠 AI Prediction\nTomorrow's expected OPD\n**26,800 Patients**")
    with i2:
        st.warning("### ⚠ Capacity Alert\nRajkot PHC-02\nExpected overload\nbetween **10 AM - 1 PM**")
        st.success("### 💡 Recommendation\nDeploy **2 additional doctors**\nto Rajkot PHC-02")

    st.markdown("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("📥 Download CSV", patient_df.to_csv(index=False), "patient_footfall.csv", mime="text/csv", use_container_width=True)
    with d2:
        st.button("📄 Export PDF", use_container_width=True)
    with d3:
        st.button("📧 Share Report", use_container_width=True)

    st.success("✅ Patient Footfall Analytics Running Successfully")
    st.caption("Live data updates every 60 seconds • FastAPI • Firebase • AI Analytics")
    # ==========================================
# 👨‍⚕️ DOCTOR ATTENDANCE PAGE
# ==========================================

elif page == "👨‍⚕ Doctor Attendance":
    st.header("👨‍⚕️ Doctor Attendance Monitoring")
    st.caption("Real-time monitoring of doctor availability across PHCs")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="doc_district")
    with f2:
        phc = st.selectbox("PHC", ["All PHCs", "PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05"], key="doc_phc")
    with f3:
        status = st.selectbox("Status", ["All", "Present", "Absent", "On Leave"], key="doc_status")
    with f4:
        st.date_input("Date", key="doc_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Doctors Present", "348", "+12", "👨‍⚕️")
    with c2:
        card("Doctors Absent", "18", "-3", "❌")
    with c3:
        card("Attendance", "95.1%", "+1.6%", "📈")
    with c4:
        card("On Leave", "11", "+2", "🏖️")

    st.markdown("---")

    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Attendance": [91, 93, 95, 96, 94, 97, 95]
        })
        fig = px.line(trend, x="Day", y="Attendance", markers=True, color_discrete_sequence=["#2563EB"])
        fig.update_layout(template="plotly_white", height=420, title="Weekly Attendance Trend")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        pie = pd.DataFrame({
            "Status": ["Present", "Absent", "Leave"],
            "Doctors": [348, 18, 11]
        })
        fig = px.pie(
            pie, names="Status", values="Doctors", hole=.55, color="Status",
            color_discrete_map={"Present": "#22C55E", "Absent": "#EF4444", "Leave": "#F59E0B"}
        )
        fig.update_layout(template="plotly_white", height=420, title="Attendance Status")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District-wise Attendance")
    
    district_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Attendance": [98, 96, 95, 94, 91, 93]
    })
    fig = px.bar(district_df, x="District", y="Attendance", color="Attendance", color_continuous_scale="Greens")
    fig.update_layout(template="plotly_white", height=420, title="Attendance Percentage", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        arrival = pd.DataFrame({
            "Time": ["8 AM", "9 AM", "10 AM", "11 AM", "12 PM"],
            "Doctors": [45, 122, 138, 38, 15]
        })
        fig = px.bar(arrival, x="Time", y="Doctors", color="Doctors", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=380, title="Doctor Arrival Time", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        speciality = pd.DataFrame({
            "Department": ["General", "Pediatrics", "Gynecology", "Orthopedic", "ENT", "Dental"],
            "Doctors": [115, 52, 41, 36, 28, 22]
        })
        fig = px.bar(speciality, x="Department", y="Doctors", color="Doctors", color_continuous_scale="Teal")
        fig.update_layout(template="plotly_white", height=380, title="Doctors by Department", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🏥 PHC Doctor Attendance")
    
    attendance_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "PHC": ["PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05", "PHC-06"],
        "Total Doctors": [18, 15, 17, 14, 12, 10],
        "Present": [17, 14, 16, 13, 11, 10],
        "Absent": [1, 1, 1, 1, 1, 0],
        "Attendance %": [94, 93, 94, 92, 91, 100],
        "Status": ["Good", "Good", "Good", "Average", "Average", "Excellent"]
    })

    def attendance_style(val):
        if val == "Excellent":
            return "background-color:#DCFCE7;color:#166534;font-weight:bold"
        elif val == "Good":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        elif val == "Average":
            return "background-color:#FEF3C7;color:#92400E;font-weight:bold"
        return "background-color:#FEE2E2;color:#991B1B;font-weight:bold"

    st.dataframe(
        attendance_df.style.map(attendance_style, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("📉 Doctor Absentee Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        absent_df = pd.DataFrame({
            "Reason": ["Leave", "Training", "Medical", "Emergency", "Unknown"],
            "Count": [8, 4, 2, 1, 3]
        })
        fig = px.bar(absent_df, x="Reason", y="Count", color="Count", color_continuous_scale="Reds")
        fig.update_layout(template="plotly_white", height=380, title="Reasons for Absence", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        weekly_df = pd.DataFrame({
            "Week": ["W1", "W2", "W3", "W4"],
            "Absent": [24, 19, 15, 18]
        })
        fig = px.line(weekly_df, x="Week", y="Absent", markers=True)
        fig.update_layout(template="plotly_white", height=380, title="Weekly Absentee Trend")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 AI Attendance Insights")
    
    a1, a2 = st.columns(2)
    with a1:
        st.success("### ✅ Positive Insights\n• Overall attendance **95%**\n• Ahmedabad has highest attendance\n• Jamnagar achieved **100% attendance**")
        st.info("### 📈 AI Forecast\nExpected attendance tomorrow\n**96.3%**")
    with a2:
        st.warning("### ⚠ Attention Required\nBhavnagar PHC-05\nAttendance dropping for\nlast 3 days.")
        st.error("### 🚨 Recommendation\nAssign temporary doctors\nto Bhavnagar PHCs.")

    st.markdown("---")
    st.subheader("📡 Live Attendance Feed")
    
    live_feed = [
        "🟢 Dr. Patel checked in at PHC-01 (08:52 AM)",
        "🟢 Dr. Shah checked in at PHC-04 (09:01 AM)",
        "🟡 Dr. Mehta marked Leave (Rajkot)",
        "🔴 Dr. Rana absent without update",
        "🟢 Ahmedabad attendance synced",
        "🟢 Firebase attendance updated"
    ]
    for item in live_feed:
        st.info(item)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("📥 Download CSV", attendance_df.to_csv(index=False), "doctor_attendance.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.button("📄 Export PDF", use_container_width=True)
    with c3:
        st.button("📧 Notify Health Officer", use_container_width=True)

    st.success("✅ Doctor Attendance Monitoring Running Successfully")
    st.caption("Live attendance sync • FastAPI • Firebase • AI Monitoring")

# ==========================================
# 🛏️ BED AVAILABILITY PAGE
# ==========================================

elif page == "🛏 Bed Availability":
    st.header("🛏️ Bed Availability Monitoring")
    st.caption("Real-time monitoring of PHC and Hospital bed occupancy across Gujarat")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="bed_district")
    with f2:
        hospital = st.selectbox("Hospital / PHC", ["All", "Civil Hospital", "PHC-01", "PHC-02", "PHC-03", "PHC-04"], key="bed_hospital")
    with f3:
        ward = st.selectbox("Ward", ["All", "General", "ICU", "Emergency", "Maternity"], key="bed_type")
    with f4:
        st.date_input("Date", key="bed_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Total Beds", "8,420", "+45", "🛏️")
    with c2:
        card("Occupied Beds", "6,118", "72.6%", "🏥")
    with c3:
        card("Available Beds", "2,302", "+128", "✅")
    with c4:
        card("Emergency Beds", "118", "Free", "🚑")

    st.markdown("---")

    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Occupied": [5480, 5615, 5752, 5891, 6010, 6128, 6118]
        })
        fig = px.area(trend, x="Day", y="Occupied", markers=True, color_discrete_sequence=["#2563EB"])
        fig.update_layout(template="plotly_white", height=420, title="Weekly Bed Occupancy")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        pie = pd.DataFrame({
            "Status": ["Occupied", "Available"],
            "Beds": [6118, 2302]
        })
        fig = px.pie(
            pie, names="Status", values="Beds", hole=.60, color="Status",
            color_discrete_map={"Occupied": "#EF4444", "Available": "#22C55E"}
        )
        fig.update_layout(template="plotly_white", height=420, title="Current Occupancy")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District-wise Bed Occupancy")
    
    district_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Occupancy %": [92, 84, 81, 76, 69, 63]
    })
    fig = px.bar(district_df, x="District", y="Occupancy %", color="Occupancy %", color_continuous_scale="RdYlGn_r")
    fig.update_layout(template="plotly_white", height=420, title="Bed Occupancy by District", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        category = pd.DataFrame({
            "Category": ["General", "ICU", "Emergency", "Maternity"],
            "Beds": [4200, 650, 980, 2590]
        })
        fig = px.bar(category, x="Category", y="Beds", color="Beds", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=380, title="Beds by Category", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        hourly = pd.DataFrame({
            "Hour": ["6 AM", "8 AM", "10 AM", "12 PM", "2 PM", "4 PM", "6 PM"],
            "Admissions": [12, 26, 42, 57, 48, 36, 22]
        })
        fig = px.line(hourly, x="Hour", y="Admissions", markers=True)
        fig.update_layout(template="plotly_white", height=380, title="Today's Bed Admissions")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🏥 PHC Bed Availability")
    
    bed_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "PHC": ["PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05", "PHC-06"],
        "Total Beds": [150, 120, 140, 110, 90, 80],
        "Occupied": [138, 101, 112, 83, 56, 48],
        "Available": [12, 19, 28, 27, 34, 32],
        "Occupancy %": [92, 84, 80, 75, 62, 60],
        "Status": ["Critical", "High", "High", "Normal", "Available", "Available"]
    })

    def bed_status(val):
        if val == "Critical":
            return "background-color:#FEE2E2;color:#B91C1C;font-weight:bold"
        elif val == "High":
            return "background-color:#FEF3C7;color:#B45309;font-weight:bold"
        elif val == "Normal":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        return "background-color:#DCFCE7;color:#166534;font-weight:bold"

    st.dataframe(
        bed_df.style.map(bed_status, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("🏥 ICU vs General Beds")
    
    c1, c2 = st.columns(2)
    with c1:
        icu = pd.DataFrame({
            "Type": ["ICU", "General", "Emergency", "Maternity"],
            "Occupied": [540, 4015, 720, 843]
        })
        fig = px.bar(icu, x="Type", y="Occupied", color="Occupied", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=380, title="Occupied Beds", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        available = pd.DataFrame({
            "Type": ["ICU", "General", "Emergency", "Maternity"],
            "Available": [110, 1185, 260, 747]
        })
        fig = px.bar(available, x="Type", y="Available", color="Available", color_continuous_scale="Greens")
        fig.update_layout(template="plotly_white", height=380, title="Available Beds", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 AI Bed Management Insights")
    
    ai1, ai2 = st.columns(2)
    with ai1:
        st.success("### ✅ AI Findings\n• Overall occupancy **72.6%**\n• 2,302 beds available\n• Emergency beds sufficient\n• Normal utilization statewide")
        st.info("### 📈 Tomorrow Prediction\nExpected Occupancy\n**74%**\nNo major shortage predicted.")
    with ai2:
        st.warning("### ⚠ Capacity Alert\nAhmedabad Civil Hospital\nOccupancy crossed\n**90%**")
        st.error("### 🚑 Recommendation\nTransfer non-critical patients\nto nearby PHCs\nto balance utilization.")

    st.markdown("---")
    st.subheader("📡 Live Hospital Feed")
    
    updates = [
        "🟢 12 beds became available at Rajkot PHC-02",
        "🟢 Emergency ward updated successfully",
        "🟡 ICU occupancy increased in Ahmedabad",
        "🟢 Firebase synchronized latest data",
        "🟢 FastAPI updated hospital records",
        "🔵 AI occupancy prediction refreshed"
    ]
    for update in updates:
        st.info(update)

    st.markdown("---")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.download_button("📥 Download Bed Report", bed_df.to_csv(index=False), "bed_availability.csv", mime="text/csv", use_container_width=True)
    with a2:
        st.button("📄 Generate PDF", use_container_width=True)
    with a3:
        st.button("🚑 Allocate Beds", use_container_width=True)

    st.success("✅ Bed Availability Monitoring Running Successfully")
    st.caption("Live Bed Tracking • FastAPI • Firebase • AI Occupancy Prediction • Refresh Every 60 Seconds")

# ==========================================
# 🌍 OUTBREAK DETECTION PAGE
# ==========================================

elif page == "🦠 Outbreak Detection":
    st.header("🦠 Disease Outbreak Detection")
    st.caption("AI-powered early outbreak prediction and public health surveillance")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="outbreak_district")
    with f2:
        disease = st.selectbox("Disease", ["All", "Dengue", "Malaria", "Typhoid", "Covid-19", "Influenza", "Cholera"], key="outbreak_disease")
    with f3:
        period = st.selectbox("Duration", ["Today", "Last 7 Days", "Last Month", "Last Year"], key="outbreak_period")
    with f4:
        st.date_input("Date", key="outbreak_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Active Outbreaks", "12", "+2", "🦠")
    with c2:
        card("High Risk Districts", "5", "+1", "🚨")
    with c3:
        card("Patients Affected", "2,148", "+184", "🏥")
    with c4:
        card("AI Prediction Accuracy", "95.8%", "+0.7%", "🤖")

    st.markdown("---")
    
    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Week": ["W1", "W2", "W3", "W4", "W5", "W6"],
            "Cases": [180, 245, 290, 410, 520, 610]
        })
        fig = px.area(trend, x="Week", y="Cases", markers=True, color_discrete_sequence=["#EF4444"])
        fig.update_layout(template="plotly_white", height=420, title="Disease Cases Trend")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        risk = pd.DataFrame({
            "Risk": ["Critical", "High", "Medium", "Low"],
            "Districts": [2, 3, 6, 15]
        })
        fig = px.pie(
            risk, names="Risk", values="Districts", hole=.60, color="Risk",
            color_discrete_map={"Critical": "#DC2626", "High": "#F59E0B", "Medium": "#3B82F6", "Low": "#22C55E"}
        )
        fig.update_layout(template="plotly_white", height=420, title="Risk Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District Risk Level")
    
    district_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Risk Score": [94, 83, 76, 62, 48, 39]
    })
    fig = px.bar(district_df, x="District", y="Risk Score", color="Risk Score", color_continuous_scale="Reds")
    fig.update_layout(template="plotly_white", height=420, title="District-wise Outbreak Risk", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        disease_df = pd.DataFrame({
            "Disease": ["Dengue", "Malaria", "Covid", "Typhoid", "Flu"],
            "Cases": [610, 480, 320, 210, 185]
        })
        fig = px.bar(disease_df, x="Disease", y="Cases", color="Cases", color_continuous_scale="OrRd")
        fig.update_layout(template="plotly_white", height=380, title="Disease-wise Cases", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        prediction = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Predicted Cases": [240, 310, 420, 515, 640, 720]
        })
        fig = px.line(prediction, x="Month", y="Predicted Cases", markers=True, color_discrete_sequence=["#DC2626"])
        fig.update_layout(template="plotly_white", height=380, title="AI Predicted Outbreak Trend")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🚨 High Risk Hotspots")
    
    hotspot_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Disease": ["Dengue", "Malaria", "Typhoid", "Covid-19", "Influenza", "Cholera"],
        "Current Cases": [610, 480, 350, 290, 170, 95],
        "Predicted Cases": [725, 552, 418, 340, 190, 110],
        "Growth %": [18.8, 15.0, 19.4, 17.2, 11.8, 15.7],
        "Risk": ["Critical", "High", "High", "Medium", "Medium", "Low"]
    })

    def outbreak_color(val):
        if val == "Critical":
            return "background-color:#FEE2E2;color:#B91C1C;font-weight:bold"
        elif val == "High":
            return "background-color:#FEF3C7;color:#92400E;font-weight:bold"
        elif val == "Medium":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        return "background-color:#DCFCE7;color:#166534;font-weight:bold"

    st.dataframe(
        hotspot_df.style.map(outbreak_color, subset=["Risk"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("🤖 AI Early Warning System")
    
    c1, c2 = st.columns(2)
    with c1:
        prediction_df = pd.DataFrame({
            "Next Week": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar"],
            "Probability": [96, 88, 84, 61, 42]
        })
        fig = px.bar(prediction_df, x="Next Week", y="Probability", color="Probability", color_continuous_scale="Reds")
        fig.update_layout(template="plotly_white", title="Outbreak Probability", height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        trend = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Risk Score": [68, 71, 74, 82, 88, 91, 94]
        })
        fig = px.line(trend, x="Day", y="Risk Score", markers=True, color_discrete_sequence=["#DC2626"])
        fig.update_layout(template="plotly_white", title="AI Risk Score Trend", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("💡 AI Recommendations")
    
    a1, a2 = st.columns(2)
    with a1:
        st.error("### 🚨 Immediate Action\nIncrease Dengue surveillance\nAhmedabad District\nwithin next 24 hours.")
        st.warning("### ⚠ Field Investigation\nDeploy Rapid Response Team\nRajkot & Surat.")
        st.success("### 💉 Preventive Action\nIncrease medicine stock\nfor fever management.")
    with a2:
        st.info("### 🤖 AI Confidence\nPrediction Confidence\n97.2%")
        st.success("### 📈 Expected Result\nEarly intervention may reduce\ncases by **35%**")
        st.warning("### 📢 Public Awareness\nLaunch awareness campaign\nin high-risk districts.")

    st.markdown("---")
    st.subheader("📡 Live Surveillance Feed")
    
    alerts = [
        "🔴 Dengue cluster detected in Ahmedabad",
        "🟠 Malaria cases increasing in Rajkot",
        "🟢 Covid-19 cases stable",
        "🟡 Fever cases rising in Surat",
        "🟢 FastAPI surveillance updated",
        "🟢 Firebase synced latest outbreak data"
    ]
    for alert in alerts:
        st.info(alert)

    st.markdown("---")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.download_button("📥 Download Report", hotspot_df.to_csv(index=False), "outbreak_report.csv", mime="text/csv", use_container_width=True)
    with b2:
        st.button("📄 Export PDF", use_container_width=True)
    with b3:
        st.button("📧 Notify Health Department", use_container_width=True)

    st.success("✅ AI Outbreak Detection System Running Successfully")
    st.caption("FastAPI • Firebase • XGBoost • Isolation Forest • Real-time Disease Surveillance")

# ==========================================
# ⭐ TRUST SCORE PAGE
# ==========================================

elif page == "🛡 Trust Score":
    st.header("🛡 District Trust Score")
    st.caption("AI-powered credibility score based on healthcare reporting quality, anomaly detection and operational consistency.")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="trust_district")
    with f2:
        month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June"], key="trust_month")
    with f3:
        level = st.selectbox("Trust Level", ["All", "Excellent", "Good", "Average", "Poor"], key="trust_level")
    with f4:
        st.date_input("Date", key="trust_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Average Trust Score", "91.4", "+2.1%", "⭐")
    with c2:
        card("Excellent Districts", "12", "+1", "🏆")
    with c3:
        card("Suspicious Reports", "27", "-5", "🚨")
    with c4:
        card("AI Confidence", "97.1%", "+0.8%", "🤖")

    st.markdown("---")
    
    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Score": [82, 84, 86, 89, 90, 91]
        })
        fig = px.line(trend, x="Month", y="Score", markers=True, color_discrete_sequence=["#2563EB"])
        fig.update_layout(title="Average Trust Score Trend", template="plotly_white", height=420)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        trust = pd.DataFrame({
            "Category": ["Excellent", "Good", "Average", "Poor"],
            "Count": [12, 10, 4, 1]
        })
        fig = px.pie(
            trust, names="Category", values="Count", hole=.60, color="Category",
            color_discrete_map={"Excellent": "green", "Good": "royalblue", "Average": "orange", "Poor": "red"}
        )
        fig.update_layout(template="plotly_white", height=420, title="District Trust Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District-wise Trust Score")
    
    district_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Trust Score": [96, 93, 91, 88, 81, 86]
    })
    fig = px.bar(district_df, x="District", y="Trust Score", color="Trust Score", color_continuous_scale="Greens")
    fig.update_layout(template="plotly_white", height=420, title="District Trust Score", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        factors = pd.DataFrame({
            "Factor": ["Reporting Accuracy", "Data Completeness", "Stock Consistency", "Doctor Attendance", "Patient Records"],
            "Score": [97, 94, 91, 88, 90]
        })
        fig = px.bar(factors, x="Factor", y="Score", color="Score", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=380, title="Trust Score Components", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        anomaly = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Anomalies": [28, 24, 18, 15, 11, 8]
        })
        fig = px.area(anomaly, x="Month", y="Anomalies", color_discrete_sequence=["#EF4444"])
        fig.update_layout(template="plotly_white", height=380, title="Detected Anomalies")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🏆 District Trust Ranking")
    
    trust_df = pd.DataFrame({
        "Rank": [1, 2, 3, 4, 5, 6],
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Jamnagar", "Bhavnagar"],
        "Trust Score": [96, 93, 91, 88, 86, 81],
        "Anomalies": [2, 4, 6, 8, 11, 18],
        "Data Quality": ["99%", "98%", "96%", "94%", "93%", "89%"],
        "Status": ["Excellent", "Excellent", "Good", "Good", "Average", "Poor"]
    })

    def trust_style(value):
        if value == "Excellent":
            return "background-color:#DCFCE7;color:#166534;font-weight:bold"
        elif value == "Good":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        elif value == "Average":
            return "background-color:#FEF3C7;color:#92400E;font-weight:bold"
        return "background-color:#FEE2E2;color:#991B1B;font-weight:bold"

    st.dataframe(
        trust_df.style.map(trust_style, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("🚨 Suspicious Reporting Analysis")
    
    c1, c2 = st.columns(2)
    with c1:
        suspicious = pd.DataFrame({
            "District": ["Bhavnagar", "Jamnagar", "Vadodara", "Surat"],
            "Suspicious Reports": [18, 11, 8, 6]
        })
        fig = px.bar(suspicious, x="District", y="Suspicious Reports", color="Suspicious Reports", color_continuous_scale="Reds")
        fig.update_layout(template="plotly_white", height=380, title="Detected Suspicious Reports", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        quality = pd.DataFrame({
            "Category": ["Verified", "Needs Review", "Flagged"],
            "Count": [228, 31, 12]
        })
        fig = px.pie(
            quality, names="Category", values="Count", hole=.60, color="Category",
            color_discrete_map={"Verified": "green", "Needs Review": "orange", "Flagged": "red"}
        )
        fig.update_layout(template="plotly_white", height=380, title="Data Verification Status")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 AI Trust Insights")
    
    ai1, ai2 = st.columns(2)
    with ai1:
        st.success("### ✅ Best Performing District\nAhmedabad maintains the\nhighest trust score (96).\nExcellent reporting quality.")
        st.info("### 📈 Trend\nOverall trust score increased\nby **2.1%**\nduring this month.")
        st.success("### ✔ Model Confidence\nAI Trust Model\nConfidence : **97.1%**")
    with ai2:
        st.warning("### ⚠ Review Required\nBhavnagar submitted\n18 suspicious reports.\nManual verification advised.")
        st.error("### 🚨 Recommendation\nConduct field audit\nwithin next 48 hours.")
        st.info("### 🔍 AI Observation\nLow stock with\nzero consumption detected.\nPossible reporting anomaly.")

    st.markdown("---")
    st.subheader("🤖 Latest AI Recommendations")
    
    recommendation_df = pd.DataFrame({
        "Priority": ["Critical", "High", "High", "Medium", "Medium", "Low"],
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Category": ["Medicine", "Outbreak", "Doctor", "Bed", "Trust", "Medicine"],
        "Recommendation": ["Dispatch IFA Tablets", "Deploy Rapid Response Team", "Assign 2 Doctors", "Allocate 15 Beds", "Verify Monthly Report", "Routine Medicine Refill"],
        "Confidence": ["98%", "97%", "96%", "94%", "92%", "90%"],
        "Status": ["Pending", "Pending", "In Progress", "Completed", "Review", "Completed"]
    })

    def rec_status(value):
        if value == "Pending":
            return "background-color:#FEE2E2;color:#B91C1C;font-weight:bold"
        elif value == "In Progress":
            return "background-color:#FEF3C7;color:#92400E;font-weight:bold"
        elif value == "Completed":
            return "background-color:#DCFCE7;color:#166534;font-weight:bold"
        return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"

    st.dataframe(
        recommendation_df.style.map(rec_status, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("📊 AI Decision Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        decision_df = pd.DataFrame({
            "Action": ["Medicine Supply", "Doctor Allocation", "Bed Management", "Disease Alert", "Trust Review"],
            "Count": [61, 39, 28, 37, 21]
        })
        fig = px.bar(decision_df, x="Action", y="Count", color="Count", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", title="AI Suggested Actions", height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        confidence_df = pd.DataFrame({
            "Confidence": ["95-100%", "90-95%", "80-90%", "<80%"],
            "Predictions": [92, 56, 28, 10]
        })
        fig = px.pie(confidence_df, names="Confidence", values="Predictions", hole=.60)
        fig.update_layout(template="plotly_white", title="Prediction Confidence", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("💡 AI Insights")
    
    a1, a2 = st.columns(2)
    with a1:
        st.success("### ✅ Top Recommendation\nIncrease IFA Tablet stock\nAhmedabad District\nwithin next 48 hours.")
        st.info("### 📈 Forecast\nMedicine demand expected\nto increase by **18%**\nnext week.")
        st.success("### 🤖 AI Confidence\nCurrent Model Confidence\n**96.8%**")
    with a2:
        st.warning("### ⚠ Workforce Alert\nRajkot requires\n2 additional doctors.")
        st.error("### 🚨 Outbreak Warning\nPotential Dengue cluster\npredicted in Ahmedabad.")
        st.info("### 🛏 Capacity Suggestion\nShift patients to\nnearby PHCs.")

    st.markdown("---")
    st.subheader("📡 Live AI Recommendation Feed")
    
    feed = [
        "🤖 AI generated new medicine allocation plan",
        "🟢 Stock redistribution completed",
        "🟡 Doctor shortage detected in Rajkot",
        "🔴 High outbreak probability detected",
        "🟢 Trust score recalculated",
        "🟢 FastAPI recommendation engine updated",
        "🟢 Firebase synchronized recommendations"
    ]
    for item in feed:
        st.info(item)

    st.markdown("---")
    
    b1, b2, b3 = st.columns(3)
    with b1:
        st.download_button("📥 Download Recommendations", recommendation_df.to_csv(index=False), "ai_recommendations.csv", mime="text/csv", use_container_width=True)
    with b2:
        st.button("📄 Export PDF", use_container_width=True)
    with b3:
        st.button("🚀 Apply AI Recommendations", use_container_width=True)

    st.success("✅ AI Recommendation Engine Running Successfully")
    st.caption("Powered by XGBoost • Isolation Forest • FastAPI • Firebase • Google Build with AI")

# ==========================================
# 📊 ANALYTICS PAGE
# ==========================================

elif page == "📊 Analytics":
    st.header("📊 Healthcare Analytics Dashboard")
    st.caption("Advanced analytics and insights from Gujarat Healthcare Supply Chain")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["All", "Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="analytics_district")
    with f2:
        duration = st.selectbox("Duration", ["Last 7 Days", "Last Month", "Last Quarter", "Last Year"], key="analytics_duration")
    with f3:
        metric = st.selectbox("Analytics", ["Overall", "Stock", "Patients", "Doctors", "Beds", "Trust"], key="analytics_metric")
    with f4:
        st.date_input("Date", key="analytics_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Total PHCs", "1,486", "+12", "🏥")
    with c2:
        card("Patients", "3.28M", "+7.8%", "👨‍⚕️")
    with c3:
        card("Medicines", "248K", "+12%", "💊")
    with c4:
        card("AI Accuracy", "96.8%", "+0.4%", "🤖")

    st.markdown("---")

    left, right = st.columns([2, 1])
    with left:
        trend = pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Patients": [42000, 44800, 48200, 51400, 56100, 60300]
        })
        fig = px.line(trend, x="Month", y="Patients", markers=True, color_discrete_sequence=["#2563EB"])
        fig.update_layout(template="plotly_white", height=420, title="Monthly Patient Growth")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        pie = pd.DataFrame({
            "Category": ["Medicine", "Doctors", "Beds", "Others"],
            "Value": [41, 24, 22, 13]
        })
        fig = px.pie(pie, names="Category", values="Value", hole=.60)
        fig.update_layout(template="plotly_white", title="Healthcare Resource Distribution", height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📍 District Performance")
    
    performance = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Performance": [96, 93, 91, 88, 82, 86]
    })
    fig = px.bar(performance, x="District", y="Performance", color="Performance", color_continuous_scale="Viridis")
    fig.update_layout(template="plotly_white", title="District Performance Score", height=420, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        stock = pd.DataFrame({
            "Medicine": ["IFA", "ORS", "PCM", "TT", "Vit-A"],
            "Consumption": [4200, 3600, 3100, 2400, 1800]
        })
        fig = px.bar(stock, x="Medicine", y="Consumption", color="Consumption", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", title="Medicine Consumption", height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        opd = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "OPD": [820, 910, 1015, 1180, 1260, 1105, 980]
        })
        fig = px.area(opd, x="Day", y="OPD", color_discrete_sequence=["#10B981"])
        fig.update_layout(template="plotly_white", title="Weekly OPD Trend", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 District Analytics Summary")
    
    analytics_df = pd.DataFrame({
        "District": ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"],
        "Patients": [60300, 48700, 52800, 44200, 31500, 35200],
        "Trust Score": [96, 93, 91, 88, 82, 86],
        "Medicine Availability": ["98%", "96%", "95%", "92%", "89%", "91%"],
        "Doctor Attendance": ["97%", "95%", "94%", "92%", "90%", "91%"],
        "Performance": ["Excellent", "Excellent", "Good", "Good", "Average", "Good"]
    })

    def analytics_style(value):
        if value == "Excellent":
            return "background-color:#DCFCE7;color:#166534;font-weight:bold"
        elif value == "Good":
            return "background-color:#DBEAFE;color:#1D4ED8;font-weight:bold"
        return "background-color:#FEF3C7;color:#92400E;font-weight:bold"

    st.dataframe(
        analytics_df.style.map(analytics_style, subset=["Performance"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    st.subheader("📈 Overall Performance Comparison")
    
    col1, col2 = st.columns(2)
    with col1:
        comparison = pd.DataFrame({
            "Module": ["Medicine", "Doctors", "Beds", "Trust", "Outbreak"],
            "Score": [96, 93, 91, 95, 89]
        })
        fig = px.bar(comparison, x="Module", y="Score", color="Score", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", title="System Performance", height=380, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        radar = pd.DataFrame({
            "Category": ["Accuracy", "Speed", "Coverage", "Reliability", "Prediction"],
            "Value": [97, 95, 92, 96, 94]
        })
        fig = px.line_polar(radar, r="Value", theta="Category", line_close=True)
        fig.update_layout(template="plotly_white", title="AI Performance Radar", height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 AI Analytics Insights")
    
    a1, a2 = st.columns(2)
    with a1:
        st.success("### 📈 Overall Healthcare Improved\nOverall district performance\nimproved by **8.4%**\nover last month.")
        st.info("### 💊 Medicine Supply\nStock availability reached\n**96% statewide**")
        st.success("### 🏥 PHC Performance\nTop Performing District\n**Ahmedabad**")
    with a2:
        st.warning("### ⚠ Attention Required\nBhavnagar requires\nadditional medical resources.")
        st.error("### 🚨 Critical Alert\nHigh patient load\nexpected next week.")
        st.info("### 🤖 AI Forecast\nDemand expected to grow\nby **14%**\nnext month.")

    st.markdown("---")
    st.subheader("📡 Live Analytics Feed")
    
    feed = [
        "🟢 Dashboard refreshed successfully",
        "🟢 FastAPI synchronized latest analytics",
        "🟢 Firebase database updated",
        "📈 Patient analytics recalculated",
        "💊 Medicine analytics updated",
        "🤖 AI prediction engine refreshed",
        "⭐ Trust score recalculated",
        "🚨 Outbreak monitoring completed"
    ]
    for item in feed:
        st.info(item)

    st.markdown("---")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.download_button("📥 Download Analytics", analytics_df.to_csv(index=False), "analytics_report.csv", mime="text/csv", use_container_width=True)
    with b2:
        st.button("📄 Export PDF Report", use_container_width=True)
    with b3:
        st.button("📊 Generate Executive Report", use_container_width=True)

    st.success("✅ Healthcare Analytics Dashboard Running Successfully")
    st.caption("Google Build with AI • XGBoost • Isolation Forest • FastAPI • Firebase • Streamlit • Team AstraSync")

# ==========================================
# 🏥 PHC DATA ENTRY PAGE
# ==========================================

elif page == "🏥 PHC Data Entry":
    st.header("🏥 PHC Data Entry Portal")
    st.caption("Real-time Primary Health Centre Data Collection • Google Build with AI • FastAPI • Firebase")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        district = st.selectbox("District", ["Ahmedabad", "Rajkot", "Surat", "Vadodara", "Bhavnagar", "Jamnagar"], key="entry_district")
    with f2:
        block = st.selectbox("Block", ["Block A", "Block B", "Block C", "Block D"], key="entry_block")
    with f3:
        phc = st.selectbox("PHC Name", ["PHC-01", "PHC-02", "PHC-03", "PHC-04", "PHC-05"], key="entry_phc")
    with f4:
        entry_date = st.date_input("Entry Date", key="entry_date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("District", district, "Current Selected", "📍")
    with c2:
        card("PHC", phc, "Live Centre", "🏥")
    with c3:
        card("Operator", "District Officer", "Logged In", "👨‍⚕️")
    with c4:
        card("Status", "ONLINE", "Connected", "🟢")

    st.markdown("---")
    st.subheader("💊 Medicine Stock Entry")
    
    with st.form("medicine_stock_form"):
        m1, m2 = st.columns(2)
        with m1:
            medicine = st.selectbox("Medicine", ["IFA Tablets", "Paracetamol", "ORS", "Vitamin A", "TT Injection", "Amoxicillin", "Iron Syrup", "Calcium Tablets"])
            opening_stock = st.number_input("Opening Stock", min_value=0, value=500)
            received_stock = st.number_input("Received Today", min_value=0, value=100)
        with m2:
            consumed_stock = st.number_input("Consumed", min_value=0, value=75)
            damaged_stock = st.number_input("Damaged / Expired", min_value=0, value=2)
            remarks = st.text_area("Remarks", placeholder="Enter additional remarks...")

        current_stock = (opening_stock + received_stock - consumed_stock - damaged_stock)
        st.metric("Current Available Stock", current_stock)
        
        submitted = st.form_submit_button("💾 Save Medicine Entry", use_container_width=True)
        if submitted:
            medicine_record = pd.DataFrame({
                "Date": [entry_date],
                "District": [district],
                "Block": [block],
                "PHC": [phc],
                "Medicine": [medicine],
                "Opening Stock": [opening_stock],
                "Received": [received_stock],
                "Consumed": [consumed_stock],
                "Damaged": [damaged_stock],
                "Current Stock": [current_stock],
                "Remarks": [remarks]
            })
            st.session_state["medicine_entry"] = medicine_record
            st.success("✅ Medicine stock saved successfully.")

    st.markdown("---")
    st.subheader("🩺 OPD Patient Entry")
    
    with st.form("opd_form"):
        c1, c2 = st.columns(2)
        with c1:
            male_patients = st.number_input("Male Patients", min_value=0, value=45)
            female_patients = st.number_input("Female Patients", min_value=0, value=52)
            child_patients = st.number_input("Children", min_value=0, value=28)
        with c2:
            emergency_patients = st.number_input("Emergency Cases", min_value=0, value=7)
            referred_patients = st.number_input("Referred Patients", min_value=0, value=4)
            total_patients = (male_patients + female_patients + child_patients + emergency_patients)
            st.metric("Today's Total OPD", total_patients)

        opd_submit = st.form_submit_button("💾 Save OPD Entry", use_container_width=True)
        if opd_submit:
            st.session_state["opd_data"] = {
                "District": district, "Block": block, "PHC": phc,
                "Male": male_patients, "Female": female_patients, "Children": child_patients,
                "Emergency": emergency_patients, "Referred": referred_patients, "Total": total_patients
            }
            st.success("✅ OPD data saved successfully.")

    st.markdown("---")
    st.subheader("👨‍⚕️ Doctor Attendance")
    
    with st.form("doctor_form"):
        d1, d2 = st.columns(2)
        with d1:
            total_doctors = st.number_input("Total Doctors", min_value=1, value=5)
            present_doctors = st.number_input("Doctors Present", min_value=0, max_value=total_doctors, value=4)
        with d2:
            absent_doctors = total_doctors - present_doctors
            attendance = round((present_doctors / total_doctors) * 100, 2)
            st.metric("Attendance %", f"{attendance}%")
            st.metric("Absent Doctors", absent_doctors)

        doctor_submit = st.form_submit_button("💾 Save Attendance", use_container_width=True)
        if doctor_submit:
            st.session_state["doctor_data"] = {
                "District": district, "PHC": phc, "Present": present_doctors,
                "Total": total_doctors, "Attendance": attendance
            }
            st.success("✅ Doctor attendance saved successfully.")

    st.markdown("---")
    st.subheader("🛏 Bed Availability Entry")
    
    with st.form("bed_form"):
        b1, b2 = st.columns(2)
        with b1:
            total_beds = st.number_input("Total Beds", min_value=1, value=40)
            occupied_beds = st.number_input("Occupied Beds", min_value=0, max_value=total_beds, value=26)
        with b2:
            available_beds = total_beds - occupied_beds
            occupancy = round((occupied_beds / total_beds) * 100, 2)
            st.metric("Available Beds", available_beds)
            st.metric("Occupancy %", f"{occupancy}%")

        bed_submit = st.form_submit_button("💾 Save Bed Status", use_container_width=True)
        if bed_submit:
            st.session_state["bed_data"] = {
                "District": district, "PHC": phc, "Occupied": occupied_beds,
                "Available": available_beds, "Occupancy": occupancy
            }
            st.success("✅ Bed status saved successfully.")

    st.markdown("---")
    st.subheader("✅ Validation Status")
    
    check1, check2, check3 = st.columns(3)
    with check1:
        if "medicine_entry" in st.session_state:
            st.success("✔ Medicine Data")
        else:
            st.error("✖ Medicine Missing")
    with check2:
        if "opd_data" in st.session_state:
            st.success("✔ OPD Data")
        else:
            st.error("✖ OPD Missing")
    with check3:
        if "doctor_data" in st.session_state and "bed_data" in st.session_state:
            st.success("✔ Attendance & Beds")
        else:
            st.error("✖ Incomplete Entry")

    elif page == "🏥 PHC Data Entry":
    st.header("🏥 PHC Data Entry Portal")
    
    # ... (Your existing form code for medicine, OPD, etc.) ...

    if st.button("🚀 Submit Real-Time Data to Server", type="primary"):
        # This is where you send your data to FastAPI
        payload = {
            "district": district,
            "phc_name": phc,
            "patient_footfall": total_patients
            # ... add other fields here
        }
        
        try:
            response = requests.post(f"{API_URL}/api/phc", json=payload)
            if response.status_code == 201:
                st.success("✅ Data saved successfully!")
                
                # THIS IS THE KEY TO REAL-TIME UPDATES:
                # It forces the dashboard to re-fetch the new data
                st.cache_data.clear() 
            else:
                st.error("❌ Failed to save data.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

    st.info("Fill all sections before submitting data to the AI Pipeline.")

# ==========================================
# ⚙️ PIPELINE STATUS PAGE
# ==========================================

elif page == "⚙ Pipeline Status":
    st.header("⚙️ AI Pipeline Monitoring")
    st.caption("Monitor ML Pipeline • FastAPI • Firebase • Data Quality • Model Performance")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        pipeline = st.selectbox("Pipeline", ["Healthcare Pipeline", "Medicine Prediction", "Anomaly Detection", "Trust Score", "Outbreak Detection"])
    with f2:
        status = st.selectbox("Status", ["All", "Running", "Completed", "Failed"])
    with f3:
        refresh = st.selectbox("Refresh", ["30 Seconds", "1 Minute", "5 Minutes"])
    with f4:
        st.date_input("Run Date")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Pipeline Status", "Running", "Healthy", "🟢")
    with c2:
        card("Last Run", "10:42 AM", "2 mins ago", "⏱")
    with c3:
        card("Success Rate", "98.7%", "+0.5%", "✅")
    with c4:
        card("Model Accuracy", "96.8%", "+0.3%", "🤖")

    st.markdown("---")
    st.subheader("🚀 Current Pipeline Progress")
    
    progress = 86
    st.progress(progress / 100)
    st.success(f"Pipeline Execution : {progress}% Completed")

    st.markdown("---")
    
    stage_df = pd.DataFrame({
        "Stage": ["Load Dataset", "Data Cleaning", "Feature Engineering", "Medicine Prediction", "Anomaly Detection", "Trust Score", "Recommendation Engine", "Export Results"],
        "Status": ["Completed", "Completed", "Completed", "Completed", "Running", "Pending", "Pending", "Pending"]
    })

    def stage_color(v):
        if v == "Completed":
            return "background:#DCFCE7;color:#166534;font-weight:bold"
        elif v == "Running":
            return "background:#DBEAFE;color:#1D4ED8;font-weight:bold"
        return "background:#FEF3C7;color:#92400E;font-weight:bold"

    st.dataframe(
        stage_df.style.map(stage_color, subset=["Status"]),
        use_container_width=True, hide_index=True
    )

    st.markdown("---")
    
    left, right = st.columns(2)
    with left:
        model_df = pd.DataFrame({
            "Model": ["XGBoost", "Isolation Forest", "Random Forest", "Decision Tree"],
            "Accuracy": [96.8, 95.2, 91.4, 88.1]
        })
        fig = px.bar(model_df, x="Model", y="Accuracy", color="Accuracy", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=380, title="Model Accuracy", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        metric_df = pd.DataFrame({
            "Metric": ["Precision", "Recall", "F1", "ROC-AUC"],
            "Value": [95.8, 94.6, 95.1, 97.4]
        })
        fig = px.bar(metric_df, x="Metric", y="Value", color="Value", color_continuous_scale="Greens")
        fig.update_layout(template="plotly_white", height=380, title="Evaluation Metrics", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📜 Pipeline Logs")
    
    logs = [
        "🟢 Dataset loaded successfully",
        "🟢 Data preprocessing completed",
        "🟢 Feature engineering completed",
        "🟢 XGBoost prediction completed",
        "🔄 Isolation Forest running",
        "⏳ Trust score calculation pending",
        "⏳ Recommendation engine waiting",
        "📦 Export will start automatically"
    ]
    for log in logs:
        st.info(log)

    st.markdown("---")
    st.subheader("📊 Data Quality Report")
    
    q1, q2, q3 = st.columns(3)
    with q1:
        st.metric("Missing Values", "0.8%")
    with q2:
        st.metric("Duplicate Records", "14")
    with q3:
        st.metric("Valid Records", "99.2%")

    st.markdown("---")
    
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("🚀 Run Pipeline", use_container_width=True):
            st.success("Pipeline Started Successfully")
    with a2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with a3:
        st.download_button("📥 Download Logs", "\n".join(logs), file_name="pipeline_logs.txt", mime="text/plain", use_container_width=True)
    with a4:
        st.button("📄 Generate Report", use_container_width=True)

    st.markdown("---")
    st.subheader("🖥 System Health")
    
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.success("🟢 FastAPI Online")
    with h2:
        st.success("🟢 Firebase Connected")
    with h3:
        st.success("🟢 Streamlit Running")
    with h4:
        st.success("🟢 ML Models Loaded")

    st.success("✅ AI Pipeline Monitoring System Running Successfully")
    st.caption("Google Build with AI • FastAPI • Firebase • Streamlit • XGBoost • Isolation Forest • Team AstraSync")