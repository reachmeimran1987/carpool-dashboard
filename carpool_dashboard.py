
import streamlit as st
import pandas as pd
import datetime
from collections import defaultdict

if 'attendance' not in st.session_state:
    st.session_state.attendance = {}
if 'quickride' not in st.session_state:
    st.session_state.quickride = {}
if 'drivers' not in st.session_state:
    st.session_state.drivers = {}
if 'members' not in st.session_state:
    st.session_state.members = []

st.title("🚗 Pro Carpool Cost Sharing Dashboard")

st.subheader("1. Regular Carpool Members")
members_input = st.text_input("Enter regular members (comma-separated)", value=", ".join(st.session_state.members))
if st.button("Update Members"):
    st.session_state.members = [m.strip() for m in members_input.split(',') if m.strip()]

st.subheader("2. Daily Attendance Entry & Edit")
date = st.date_input("Select date", datetime.date.today())
date_str = date.isoformat()

for session in ["Morning", "Evening"]:
    st.markdown(f"### {session} Ride")
    key = f"{date_str}_{session}"
    existing_attendees = st.session_state.attendance.get(key, [])
    existing_qr = st.session_state.quickride.get(key, 0.0)
    existing_driver = st.session_state.drivers.get(key, "")

    attendees = st.multiselect(f"Select attendees for {session.lower()} ride", st.session_state.members + ["QuickRide Guest"], default=existing_attendees, key=f"attendees_{session}")
    quickride_amount = st.number_input(f"QuickRide earnings for {session.lower()} ride (₹)", min_value=0.0, value=float(existing_qr), step=10.0, key=f"qr_{session}")
    driver = st.selectbox(f"Select driver for {session.lower()} ride", [""] + st.session_state.members, index=st.session_state.members.index(existing_driver) + 1 if existing_driver in st.session_state.members else 0, key=f"driver_{session}")

    if st.button(f"Save {session} Entry"):
        st.session_state.attendance[key] = attendees
        st.session_state.quickride[key] = quickride_amount
        st.session_state.drivers[key] = driver
        st.success(f"{session} data saved for {date_str}")

def calculate_weekly_settlement(regular_members, daily_attendance, quickride_earnings, driver_selection, session_cost=375.0):
    weekly_totals = defaultdict(float)
    driver_earnings = defaultdict(float)
    daily_breakdown = {}

    for key, attendees in daily_attendance.items():
        regulars_today = [p for p in attendees if p in regular_members]
        quickride_today = quickride_earnings.get(key, 0.0)
        driver = driver_selection.get(key, None)

        if not regulars_today:
            daily_breakdown[key] = {"note": "No regular members present"}
            continue

        net_cost = session_cost - quickride_today
        cost_per_person = round(net_cost / len(regulars_today))

        for person in regulars_today:
            weekly_totals[person] += cost_per_person

        if driver in regulars_today:
            driver_earnings[driver] += net_cost

        daily_breakdown[key] = {
            "regulars": regulars_today,
            "quickride_earning": quickride_today,
            "net_cost": net_cost,
            "cost_per_person": cost_per_person,
            "driver": driver,
            "individual_shares": {p: cost_per_person for p in regulars_today}
        }

    settlements = {}
    for member in regular_members:
        paid = driver_earnings.get(member, 0)
        owes = weekly_totals.get(member, 0)
        settlements[member] = round(paid - owes)

    return daily_breakdown, dict(weekly_totals), dict(driver_earnings), settlements

if st.button("Calculate Weekly Settlement"):
    daily_summary, weekly_summary, driver_earnings, settlements = calculate_weekly_settlement(
        st.session_state.members,
        st.session_state.attendance,
        st.session_state.quickride,
        st.session_state.drivers
    )

    st.subheader("📅 Daily Breakdown")
    for key, info in sorted(daily_summary.items()):
        st.markdown(f"**{key}**")
        st.json(info)

    st.subheader("📈 Weekly Totals")
    df_weekly = pd.DataFrame.from_dict(weekly_summary, orient='index', columns=['Amount to Pay (₹)'])
    df_weekly.index.name = 'Member'
    df_weekly['Amount to Pay (₹)'] = df_weekly['Amount to Pay (₹)'].map(lambda x: f"₹{x:,.2f}")
    st.table(df_weekly)

    st.subheader("🚘 Driver Earnings")
    df_driver = pd.DataFrame.from_dict(driver_earnings, orient='index', columns=['Earned (₹)'])
    df_driver.index.name = 'Driver'
    df_driver['Earned (₹)'] = df_driver['Earned (₹)'].map(lambda x: f"₹{x:,.2f}")
    st.table(df_driver)

    st.subheader("💰 Net Settlements")
    st.markdown("**Positive = To Receive, Negative = To Pay**")
    df_settle = pd.DataFrame.from_dict(settlements, orient='index', columns=['Net (₹)'])
    df_settle.index.name = 'Member'
    df_settle['Net (₹)'] = df_settle['Net (₹)'].map(lambda x: f"₹{x:+,.0f}")
    st.table(df_settle)

if st.button("Export to Excel"):
    df_attendance = pd.DataFrame.from_dict(st.session_state.attendance, orient='index').transpose()
    df_quickride = pd.DataFrame(list(st.session_state.quickride.items()), columns=['Session', 'QuickRide Earnings'])
    df_driver = pd.DataFrame(list(st.session_state.drivers.items()), columns=['Session', 'Driver'])
    df_weekly = pd.DataFrame.from_dict(weekly_summary, orient='index', columns=['Amount to Pay (₹)'])
    df_driver_earn = pd.DataFrame.from_dict(driver_earnings, orient='index', columns=['Earned (₹)'])
    df_settle = pd.DataFrame.from_dict(settlements, orient='index', columns=['Net (₹)'])

    with pd.ExcelWriter("carpool_summary.xlsx", engine='openpyxl') as writer:
        df_attendance.to_excel(writer, sheet_name='Attendance')
        df_quickride.to_excel(writer, sheet_name='QuickRide')
        df_driver.to_excel(writer, sheet_name='Drivers')
        df_weekly.to_excel(writer, sheet_name='Weekly Totals')
        df_driver_earn.to_excel(writer, sheet_name='Driver Earnings')
        df_settle.to_excel(writer, sheet_name='Settlements')

    st.success("Data exported to carpool_summary.xlsx")
