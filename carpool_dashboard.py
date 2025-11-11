
import streamlit as st
import pandas as pd
import datetime
from collections import defaultdict

# Initialize session state for persistent data
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}
if 'quickride' not in st.session_state:
    st.session_state.quickride = {}
if 'members' not in st.session_state:
    st.session_state.members = []

st.title("🚗 Carpool Cost Sharing Dashboard")

# Input regular members
st.subheader("1. Regular Carpool Members")
members_input = st.text_input("Enter regular members (comma-separated)", value=", ".join(st.session_state.members))
if st.button("Update Members"):
    st.session_state.members = [m.strip() for m in members_input.split(',') if m.strip()]

# Input daily attendance
st.subheader("2. Daily Attendance")
date = st.date_input("Select date", datetime.date.today())
attendees = st.multiselect("Select attendees for the day", st.session_state.members + ["QuickRide Guest"])
quickride_amount = st.number_input("QuickRide earnings for the day (₹)", min_value=0.0, value=0.0, step=10.0)

if st.button("Submit Day's Data"):
    date_str = date.isoformat()
    st.session_state.attendance[date_str] = attendees
    st.session_state.quickride[date_str] = quickride_amount
    st.success(f"Data saved for {date_str}")

# Weekly settlement calculation
def calculate_weekly_settlement(regular_members, daily_attendance, quickride_earnings, daily_ride_cost=375.0):
    weekly_totals = defaultdict(float)
    daily_breakdown = {}

    for day, attendees in daily_attendance.items():
        regulars_today = [p for p in attendees if p in regular_members]
        quickride_today = quickride_earnings.get(day, 0.0)

        if not regulars_today:
            daily_breakdown[day] = {"note": "No regular members present"}
            continue

        net_cost = daily_ride_cost - quickride_today
        cost_per_person = round(net_cost / len(regulars_today))  # Rounded off

        for person in regulars_today:
            weekly_totals[person] += cost_per_person

        daily_breakdown[day] = {
            "regulars": regulars_today,
            "quickride_earning": quickride_today,
            "net_cost": net_cost,
            "cost_per_person": cost_per_person,
            "individual_shares": {p: cost_per_person for p in regulars_today}
        }

    return daily_breakdown, dict(weekly_totals)

# Display weekly summary
if st.button("Calculate Weekly Settlement"):
    daily_summary, weekly_summary = calculate_weekly_settlement(
        st.session_state.members,
        st.session_state.attendance,
        st.session_state.quickride
    )

    st.subheader("📅 Daily Breakdown")
    for day, info in sorted(daily_summary.items()):
        st.markdown(f"**{day}**")
        st.json(info)

    st.subheader("📊 Weekly Totals")
    st.table(pd.DataFrame.from_dict(weekly_summary, orient='index', columns=['Amount to Pay (₹)']))

# Optionally save to Excel
if st.button("Export to Excel"):
    df_attendance = pd.DataFrame.from_dict(st.session_state.attendance, orient='index').transpose()
    df_quickride = pd.DataFrame(list(st.session_state.quickride.items()), columns=['Date', 'QuickRide Earnings'])
    df_weekly = pd.DataFrame.from_dict(weekly_summary, orient='index', columns=['Amount to Pay (₹)'])

    with pd.ExcelWriter("carpool_summary.xlsx", engine='openpyxl') as writer:
        df_attendance.to_excel(writer, sheet_name='Attendance')
        df_quickride.to_excel(writer, sheet_name='QuickRide')
        df_weekly.to_excel(writer, sheet_name='Weekly Totals')

    st.success("Data exported to carpool_summary.xlsx")
