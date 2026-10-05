import os
import html
import json
import re
import textwrap
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from reservation import (
    TOTAL_SEATS,
    ECONOMY_PRICE,
    BUSINESS_PRICE,
    Customer,
    Staff,
    get_seat_label,
    get_seat_class,
    get_seat_price,
    load_sample_bookings,
)


# ============================================================
# PARWAAZ - APP CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Parwaaz | پرواز",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENVIRONMENT / API KEY
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STAFF_PASSWORD = os.getenv("STAFF_PASSWORD", "admin123")


# ============================================================
# COLORS
# ============================================================

DEEP_GREEN = "#01411C"
GOLD = "#C9A227"
LIGHT_GOLD = "#F5E9B8"
WHITE = "#FFFFFF"
BACKGROUND = "#F6F8F5"
DARK = "#102218"
MUTED = "#64746A"
RED = "#D64545"
GREEN = "#198754"

# Demo flight options. All options use the same 30-seat demo inventory.
FLIGHT_OPTIONS = [
    {"flight": "PK-301", "route": "Lahore → Dubai", "date": "12 October 2026", "time": "09:30 PKT", "gate": "A7"},
    {"flight": "PK-214", "route": "Lahore → Karachi", "date": "13 October 2026", "time": "11:00 PKT", "gate": "B2"},
    {"flight": "PK-410", "route": "Islamabad → Dubai", "date": "14 October 2026", "time": "14:30 PKT", "gate": "C4"},
    {"flight": "PK-520", "route": "Karachi → Jeddah", "date": "15 October 2026", "time": "18:45 PKT", "gate": "A3"},
    {"flight": "PK-630", "route": "Peshawar → Doha", "date": "16 October 2026", "time": "20:15 PKT", "gate": "B5"},
    {"flight": "PK-710", "route": "Multan → Islamabad", "date": "17 October 2026", "time": "08:15 PKT", "gate": "C1"},
]

LANGUAGE_TEXT = {
    "English": {
        "customer": "Customer Portal",
        "book": "Book a Seat",
        "cancel": "Cancel Booking",
        "my_booking": "My Booking",
        "available": "Available Seats",
        "book_title": "Book Your Flight",
        "name": "Passenger Name",
        "phone": "Pakistani Phone Number",
        "flight": "Select Flight",
        "seat": "Select Seat",
        "payment": "Payment Method",
        "confirm": "Confirm Booking",
        "cancel_title": "Cancel a Booking",
        "find": "Find Booking",
    },
    "Urdu": {
        "customer": "مسافر پورٹل",
        "book": "سیٹ بک کریں",
        "cancel": "بکنگ منسوخ کریں",
        "my_booking": "میری بکنگ",
        "available": "دستیاب سیٹس",
        "book_title": "اپنی پرواز بک کریں",
        "name": "مسافر کا نام",
        "phone": "پاکستانی فون نمبر",
        "flight": "پرواز منتخب کریں",
        "seat": "سیٹ منتخب کریں",
        "payment": "ادائیگی کا طریقہ",
        "confirm": "بکنگ کی تصدیق کریں",
        "cancel_title": "بکنگ منسوخ کریں",
        "find": "بکنگ تلاش کریں",
    },
}


def is_valid_pk_phone(phone):
    return bool(re.fullmatch(r"\+92 3\d{2} \d{7}", phone.strip()))


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():
    """Create all Streamlit session variables once."""

    if "passenger_names" not in st.session_state:
        st.session_state.passenger_names = ["Empty"] * TOTAL_SEATS

    if "seat_status" not in st.session_state:
        st.session_state.seat_status = ["Available"] * TOTAL_SEATS

    if "sample_data_loaded" not in st.session_state:
        load_sample_bookings(
            st.session_state.passenger_names,
            st.session_state.seat_status,
        )
        st.session_state.sample_data_loaded = True

    if "activity_log" not in st.session_state:
        st.session_state.activity_log = []

    if "last_booking" not in st.session_state:
        st.session_state.last_booking = None

    if "staff_logged_in" not in st.session_state:
        st.session_state.staff_logged_in = False

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "language" not in st.session_state:
        st.session_state.language = "English"

    if "selected_flight" not in st.session_state:
        st.session_state.selected_flight = FLIGHT_OPTIONS[0]

    if "passenger_phones" not in st.session_state:
        st.session_state.passenger_phones = {}


initialize_session_state()


# ============================================================
# OBJECTS
# ============================================================

customer = Customer(
    st.session_state.passenger_names,
    st.session_state.seat_status,
)

staff = Staff(
    st.session_state.passenger_names,
    st.session_state.seat_status,
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {{
        --green: {DEEP_GREEN};
        --green2: #006B35;
        --green3: #0B8A4A;
        --gold: {GOLD};
        --ink: {DARK};
        --muted: {MUTED};
        --border: #DCE7E0;
        --surface: #FFFFFF;
        --soft: #F4F8F5;
        --red: {RED};
    }}

    * {{ font-family: 'Manrope', sans-serif; box-sizing: border-box; }}
    .stApp {{
        background:
            radial-gradient(circle at 82% 0%, rgba(201,162,39,.10), transparent 24%),
            radial-gradient(circle at 10% 20%, rgba(0,107,53,.035), transparent 22%),
            #F5F8F6;
        color: var(--ink);
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    section[data-testid="stSidebar"] {{
        width: 255px !important;
        min-width: 255px !important;
        background: linear-gradient(180deg, #013D1A 0%, #003216 55%, #00270F 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }}
    section[data-testid="stSidebar"] > div {{ width: 255px !important; }}
    section[data-testid="stSidebar"] .block-container {{ padding: 22px 17px 24px !important; }}

    [data-testid="stSidebar"] [data-testid="stSelectbox"] label {{ color:#FFF !important; font-weight:700 !important; }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] {{
        background:#FFF !important; border:0 !important; border-radius:10px !important; min-height:40px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] input {{ color:#102218 !important; -webkit-text-fill-color:#102218 !important; }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {{ fill:#102218 !important; color:#102218 !important; }}
    [data-baseweb="popover"], [data-baseweb="popover"] > div {{ background:#FFF !important; }}
    [data-baseweb="popover"] [role="option"], [data-baseweb="popover"] [role="option"] * {{ color:#102218 !important; background:#FFF !important; }}

    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        border-radius:10px !important; padding:10px 11px !important; margin:2px 0 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background:rgba(255,255,255,.08) !important; }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] label span {{ color:#FFF !important; font-weight:600 !important; }}

    .block-container {{ max-width: 1480px !important; padding: 26px 42px 65px !important; }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border:1px solid var(--border) !important;
        border-radius:18px !important;
        background:rgba(255,255,255,.96) !important;
        box-shadow:0 8px 26px rgba(16,34,24,.045) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius:18px !important; }}

    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea {{
        border-radius:10px !important; border:1px solid #D4E0D8 !important; background:#FFF !important;
        color:#102218 !important; box-shadow:none !important;
    }}
    div[data-baseweb="select"] > div:focus-within,
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {{
        border-color:#00723A !important; box-shadow:0 0 0 3px rgba(0,107,53,.08) !important;
    }}

    button[data-baseweb="tab"] {{ font-weight:700 !important; color:#718078 !important; padding:12px 15px !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:var(--green) !important; }}
    div[data-baseweb="tab-highlight"] {{ background:var(--gold) !important; height:3px !important; border-radius:3px !important; }}
    div[data-testid="stAlert"] {{ border-radius:12px !important; border-width:1px !important; }}

    .stButton > button {{
        border-radius:10px !important; border:1px solid #C9D8CE !important; font-weight:700 !important;
        min-height:43px !important; padding:0 18px !important; transition:.18s ease !important;
    }}
    .stButton > button:hover {{ border-color:var(--green) !important; transform:translateY(-1px); }}
    .stButton > button[kind="primary"] {{
        background:linear-gradient(135deg,#01411C,#00723A) !important; color:#FFF !important; border:0 !important;
        box-shadow:0 8px 18px rgba(1,65,28,.15) !important;
    }}

    /* ===== Dashboard hero ===== */
    .hero {{
        position:relative; overflow:hidden; min-height:185px; padding:32px 38px; border-radius:22px;
        color:#FFF; background:linear-gradient(120deg,#003B18 0%,#006B35 58%,#01411C 100%);
        box-shadow:0 15px 38px rgba(1,65,28,.15); margin-bottom:13px;
    }}
    .hero::after {{ content:"✈"; position:absolute; right:35px; top:3px; font-size:125px; opacity:.075; transform:rotate(-12deg); }}
    .hero-small {{ color:#E9D37A; font-size:10px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px; }}
    .hero-title {{ position:relative; z-index:2; font-size:38px; line-height:1.1; font-weight:800; letter-spacing:-1px; }}
    .gold-text {{ color:#E7CA5A; margin-left:8px; }}
    .hero-subtitle {{ position:relative; z-index:2; margin-top:7px; font-size:13px; color:rgba(255,255,255,.82); }}

    .flight-strip {{
        display:flex; align-items:center; justify-content:space-between; gap:18px; padding:14px 20px;
        margin-bottom:15px; border:1px solid var(--border); border-radius:14px; background:#FFF;
        box-shadow:0 5px 18px rgba(16,34,24,.045);
    }}
    .flight-route {{ font-size:18px; font-weight:800; color:var(--green); }}
    .flight-meta {{ color:var(--muted); font-size:11px; font-weight:600; }}

    .metric-card {{
        position:relative; min-height:122px; padding:17px 18px; background:#FFF; border:1px solid var(--border);
        border-radius:16px; box-shadow:0 6px 20px rgba(16,34,24,.045); overflow:hidden; transition:.18s ease;
    }}
    .metric-card:hover {{ transform:translateY(-2px); box-shadow:0 12px 28px rgba(16,34,24,.08); }}
    .metric-card::after {{ content:""; position:absolute; width:66px; height:66px; right:-24px; bottom:-24px; border-radius:50%; background:rgba(201,162,39,.10); }}
    .metric-icon {{ font-size:19px; margin-bottom:7px; }}
    .metric-title {{ color:var(--muted); font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.65px; }}
    .metric-value {{ color:var(--green); font-size:26px; font-weight:800; margin-top:2px; }}

    .section-title {{ color:var(--green); font-size:21px; font-weight:800; margin:24px 0 10px; letter-spacing:-.3px; }}
    .dashboard-card {{ background:#FFF; border:1px solid var(--border); border-radius:18px; padding:18px; box-shadow:0 7px 22px rgba(16,34,24,.045); min-height:100%; }}
    .dashboard-card-title {{ font-size:15px; font-weight:800; color:var(--ink); margin-bottom:8px; }}
    .detail-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:8px; }}
    .detail-item {{ padding:13px 14px; border-radius:12px; background:#F6F9F7; border:1px solid #E4ECE7; }}
    .detail-label {{ color:var(--muted); font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:.6px; }}
    .detail-value {{ color:var(--ink); font-size:13px; font-weight:700; margin-top:4px; }}

    .seat-map {{
        padding:30px 34px 24px; border:1px solid var(--border); border-radius:22px; background:linear-gradient(180deg,#FFF 0%,#F5F9F6 100%);
        box-shadow:0 10px 30px rgba(16,34,24,.055); max-width:860px; margin:0 auto 22px;
    }}
    .plane-nose {{ width:62px; height:62px; margin:0 auto 22px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:#EAF5EE; border:1px solid #D5E7DA; font-size:27px; }}
    .seat-row {{ display:flex !important; align-items:center; justify-content:center; gap:10px; margin:9px 0; min-height:45px; }}
    .row-number {{ width:28px; margin-right:4px; color:var(--muted); font-size:11px; font-weight:800; text-align:center; }}
    .seat {{ width:50px; height:43px; display:flex; align-items:center; justify-content:center; border-radius:10px; font-size:11px; font-weight:800; box-shadow:0 3px 8px rgba(16,34,24,.055); }}
    .seat.available {{ background:#E8F7EE; border:1px solid #B8DEC5; color:#11723F; }}
    .seat.booked {{ background:#FCEAEA; border:1px solid #F1BBBB; color:#C03939; }}
    .aisle {{ width:35px; }}
    .legend {{ display:flex; justify-content:center; gap:28px; margin-top:22px; color:var(--muted); font-size:11px; }}
    .legend-item {{ display:flex; align-items:center; gap:7px; }}
    .legend-box {{ width:12px; height:12px; border-radius:4px; }}

    .card {{ background:#FFF; border:1px solid var(--border); border-radius:18px; padding:22px; box-shadow:0 7px 22px rgba(16,34,24,.045); }}
    .booking-intro-card {{
        position:relative; overflow:hidden; color:#FFF;
        background:linear-gradient(120deg,#003B18 0%,#006B35 62%,#01411C 100%);
        border:1px solid rgba(1,65,28,.18); border-radius:20px; padding:25px 28px;
        box-shadow:0 12px 30px rgba(1,65,28,.13); margin-bottom:14px;
    }}
    .booking-intro-card::after {{
        content:"✈"; position:absolute; right:24px; top:3px; font-size:82px;
        opacity:.08; transform:rotate(-12deg);
    }}
    .booking-intro-card h3 {{
        position:relative; z-index:2; color:#FFF !important; font-size:26px;
        font-weight:800; margin:0 0 7px !important;
    }}
    .booking-intro-card p {{
        position:relative; z-index:2; color:rgba(255,255,255,.82) !important;
        font-size:13px; margin:0 !important;
    }}
    .info-box {{ padding:15px 17px; border-radius:13px; background:#EFF8F2; border:1px solid #D7E9DC; border-left:4px solid var(--green); margin:11px 0; }}
    .staff-login-card {{
        position:relative; overflow:hidden; color:#FFF;
        background:linear-gradient(120deg,#003B18 0%,#006B35 62%,#01411C 100%);
        border:1px solid rgba(1,65,28,.18); border-radius:20px; padding:25px 28px;
        box-shadow:0 12px 30px rgba(1,65,28,.13); margin-bottom:14px;
    }}
    .staff-login-card::after {{
        content:"🧳"; position:absolute; right:28px; top:8px; font-size:70px;
        opacity:.10; transform:rotate(-8deg);
    }}
    .staff-login-card h3 {{
        position:relative; z-index:2; color:#FFF !important; font-size:25px;
        font-weight:800; margin:0 0 7px !important;
    }}
    .staff-login-card p {{
        position:relative; z-index:2; color:rgba(255,255,255,.82) !important;
        font-size:13px; margin:0 !important;
    }}


    .warning-box {{ padding:15px 17px; border-radius:13px; background:#FFF9E8; border:1px solid #F0E1A7; border-left:4px solid var(--gold); margin:11px 0; }}

    .boarding-pass {{ overflow:hidden; margin:18px 0; border:1px solid #D8E3DB; border-radius:20px; background:#FFF; box-shadow:0 14px 35px rgba(16,34,24,.09); }}
    .ticket-header {{ padding:22px 25px; color:#FFF; background:linear-gradient(120deg,#01411C,#006B35); display:flex; justify-content:space-between; gap:20px; }}
    .ticket-title {{ font-size:21px; font-weight:800; }}
    .ticket-body {{ padding:24px 25px; background:#FFF; }}
    .ticket-label {{ color:var(--muted); font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.7px; }}
    .ticket-value {{ color:var(--ink); font-size:14px; font-weight:700; margin-top:3px; }}
    .tear-line {{ border-top:2px dashed #D9E3DC; }}
    .barcode {{ height:52px; margin-top:18px; background:repeating-linear-gradient(90deg,#102218 0,#102218 2px,transparent 2px,transparent 5px); opacity:.85; }}
    .chat-suggestion {{ background:#EDF5EF; border:1px solid #D6E5D9; padding:10px 14px; border-radius:20px; color:var(--green); font-size:13px; }}

    /* =========================================================
       PARWAAZ AI CHAT INPUT - FRIENDLY AI FACE
       The avatar sits just outside the left side of the real
       Streamlit chat input, so the existing input functionality
       stays completely unchanged.
       ========================================================= */
    [data-testid="stChatInput"] {{
        position:relative !important;
        overflow:visible !important;
    }}

    [data-testid="stChatInput"]::before {{
        content:"🤖";
        position:absolute;
        left:-58px;
        top:50%;
        transform:translateY(-50%);
        width:46px;
        height:46px;
        display:flex;
        align-items:center;
        justify-content:center;
        border-radius:50%;
        background:linear-gradient(145deg,#EAF6EE,#FFFFFF);
        border:2px solid #C9A227;
        box-shadow:0 7px 18px rgba(1,65,28,.16), 0 0 0 5px rgba(201,162,39,.08);
        font-size:25px;
        z-index:20;
        animation:parwaazAiPulse 2.8s ease-in-out infinite;
    }}

    @keyframes parwaazAiPulse {{
        0%,100% {{ box-shadow:0 7px 18px rgba(1,65,28,.16), 0 0 0 5px rgba(201,162,39,.08); }}
        50% {{ box-shadow:0 8px 22px rgba(1,65,28,.22), 0 0 0 9px rgba(201,162,39,.04); }}
    }}

    /* Bring back the playful flip-in feel for Parwaaz AI replies. */
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
        animation:parwaazAssistantFlip .62s cubic-bezier(.22,.72,.28,1.12) both;
        transform-origin:left center;
    }}

    @keyframes parwaazAssistantFlip {{
        0% {{ opacity:0; transform:perspective(900px) rotateX(-78deg) translateY(12px) scale(.96); }}
        55% {{ opacity:1; transform:perspective(900px) rotateX(10deg) translateY(-2px) scale(1.01); }}
        100% {{ opacity:1; transform:perspective(900px) rotateX(0deg) translateY(0) scale(1); }}
    }}

    @media (max-width:700px) {{
        [data-testid="stChatInput"]::before {{
            left:8px;
            top:-24px;
            width:38px;
            height:38px;
            font-size:21px;
        }}
    }}

    .footer {{ text-align:center; padding:40px 10px 15px; color:var(--muted); font-size:11px; }}

    @media (max-width: 1050px) {{
        .block-container {{ padding:22px 24px 55px !important; }}
        .flight-strip {{ flex-direction:column; align-items:flex-start; }}
    }}
    @media (max-width: 700px) {{
        section[data-testid="stSidebar"] {{ width:245px !important; min-width:245px !important; }}
        section[data-testid="stSidebar"] > div {{ width:245px !important; }}
        .block-container {{ padding:18px 14px 45px !important; }}
        .hero {{ padding:25px; min-height:160px; }}
        .hero-title {{ font-size:29px; }}
        .seat-map {{ padding:20px 7px; }}
        .seat {{ width:36px; height:36px; font-size:9px; }}
        .seat-row {{ gap:5px; }}
        .aisle {{ width:13px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def add_activity(message):
    """Add an action to the staff activity log."""

    time_now = datetime.now().strftime("%I:%M %p")

    st.session_state.activity_log.insert(
        0,
        {
            "time": time_now,
            "action": message,
        },
    )

    st.session_state.activity_log = st.session_state.activity_log[:5]


def money(amount):
    """Format PKR amount."""

    return f"Rs. {amount:,.0f}"


def get_metrics():
    """Return basic flight statistics."""

    booked = st.session_state.seat_status.count("Booked")
    available = TOTAL_SEATS - booked
    occupancy = (booked / TOTAL_SEATS) * 100

    return booked, available, occupancy


def show_metric_cards():
    """Display dashboard metrics."""

    booked, available, occupancy = get_metrics()

    cols = st.columns(4)

    metrics = [
        ("✈️", "Total Seats", TOTAL_SEATS),
        ("🎟️", "Booked", booked),
        ("💺", "Available", available),
        ("📊", "Occupancy", f"{occupancy:.0f}%"),
    ]

    for col, (icon, title, value) in zip(cols, metrics):

        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_flight_strip():
    """Display the main flight information."""

    st.markdown(
        """
        <div class="flight-strip">
            <div class="flight-route">
                PK-301 &nbsp; Lahore ✈ Dubai
            </div>
            <div class="flight-meta">
                📅 12 October 2026 &nbsp; • &nbsp;
                🕘 09:30 PKT &nbsp; • &nbsp;
                🚪 Gate A7 &nbsp; • &nbsp;
                🛫 International Flight
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_hero():
    """Display Parwaaz hero banner."""

    st.markdown(
        """
        <div class="hero">
            <div class="hero-small">PAKISTAN'S SMART TRAVEL COMPANION</div>
            <div class="hero-title">
                ✈️ Parwaaz <span class="gold-text">پرواز</span>
            </div>
            <div class="hero-subtitle">
                Every journey begins here.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_seat_map():
    """Display a clean airplane-style seat map."""

    st.markdown(
        '<div class="section-title">Choose Your Seat</div>',
        unsafe_allow_html=True,
    )

    rows_html = [
        '<div class="seat-map">',
        '<div class="plane-nose">✈️</div>',
    ]

    for row in range(1, 6):
        rows_html.append('<div class="seat-row">')
        rows_html.append(f'<div class="row-number">{row}</div>')

        for letter_index, letter in enumerate(["A", "B", "C", "D", "E", "F"]):
            if letter_index == 3:
                rows_html.append('<div class="aisle"></div>')

            seat_number = (row - 1) * 6 + letter_index + 1
            label = f"{row}{letter}"
            status = st.session_state.seat_status[seat_number - 1]
            css_class = "available" if status == "Available" else "booked"

            rows_html.append(
                f'<div class="seat {css_class}" title="{status}">{label}</div>'
            )

        rows_html.append("</div>")

    rows_html.extend([
        '<div class="legend">',
        '<div class="legend-item"><div class="legend-box" style="background:#198754;"></div>Available</div>',
        '<div class="legend-item"><div class="legend-box" style="background:#D64545;"></div>Booked</div>',
        '</div>',
        '</div>',
    ])

    st.markdown("\n".join(rows_html), unsafe_allow_html=True)

def show_donut_chart():
    """Display booked vs available donut chart."""

    booked, available, _ = get_metrics()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Booked", "Available"],
                values=[booked, available],
                hole=0.68,
                textinfo="label+percent",
                marker=dict(
                    colors=[RED, GREEN],
                    line=dict(color="white", width=3),
                ),
            )
        ]
    )

    fig.update_layout(
        title=dict(text="Seat Availability", x=0.03, xanchor="left", font=dict(size=18, color=DARK)),
        height=340,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
    )

    st.plotly_chart(
    fig,
    width="stretch"
)


def show_boarding_pass(booking):
    """Display a self-contained boarding pass after booking."""

    if not booking:
        return

    passenger = html.escape(str(booking.get("name", "")))
    flight_data = booking.get("flight", {}) or {}
    flight = html.escape(str(flight_data.get("flight", "PK-301")))
    route = html.escape(str(flight_data.get("route", "Lahore → Dubai")))
    seat = html.escape(str(booking.get("label", "")))
    seat_class = html.escape(str(booking.get("class", "Economy")))
    phone = html.escape(str(booking.get("phone", "Demo booking")))
    baggage = "40 kg" if booking.get("class") == "Business" else "30 kg"

    boarding_html = f"""
    <html>
    <head>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
                background: transparent;
            }}

            .boarding-pass {{
                max-width: 900px;
                margin: 0 auto;
                background: #ffffff;
                border: 1px solid #d9e3dc;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(1, 65, 28, 0.12);
            }}

            .ticket-header {{
                background: linear-gradient(135deg, #01411C, #086b32);
                color: white;
                padding: 24px 28px;
            }}

            .brand {{
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 6px;
            }}

            .tagline {{
                font-size: 13px;
                opacity: 0.9;
            }}

            .ticket-body {{
                padding: 26px 28px 20px;
            }}

            .passenger {{
                color: #01411C;
                font-size: 30px;
                font-weight: 800;
                margin-bottom: 22px;
            }}

            .details {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
            }}

            .detail {{
                background: #f5f8f5;
                border-radius: 12px;
                padding: 14px;
            }}

            .label {{
                color: #718078;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.7px;
                margin-bottom: 6px;
            }}

            .value {{
                color: #102218;
                font-size: 16px;
                font-weight: 700;
            }}

            .barcode {{
                height: 55px;
                margin-top: 24px;
                border-radius: 5px;
                background:
                    repeating-linear-gradient(
                        90deg,
                        #102218 0px,
                        #102218 2px,
                        transparent 2px,
                        transparent 5px,
                        #102218 5px,
                        #102218 6px,
                        transparent 6px,
                        transparent 10px
                    );
            }}

            .tear {{
                border-top: 2px dashed #d5ddd7;
                margin: 0 28px;
            }}

            .footer {{
                padding: 16px 28px 20px;
                color: #64746A;
                font-size: 12px;
            }}

            @media (max-width: 650px) {{
                .details {{
                    grid-template-columns: 1fr 1fr;
                }}

                .passenger {{
                    font-size: 24px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="boarding-pass">

            <div class="ticket-header">
                <div class="brand">✈️ Parwaaz • Boarding Pass</div>
                <div class="tagline">Every journey begins here.</div>
            </div>

            <div class="ticket-body">

                <div class="passenger">{passenger}</div>

                <div class="details">

                    <div class="detail">
                        <div class="label">Flight</div>
                        <div class="value">{flight}</div>
                    </div>

                    <div class="detail">
                        <div class="label">Route</div>
                        <div class="value">{route}</div>
                    </div>

                    <div class="detail">
                        <div class="label">Seat</div>
                        <div class="value">{seat}</div>
                    </div>

                    <div class="detail">
                        <div class="label">Class</div>
                        <div class="value">{seat_class}</div>
                    </div>

                    <div class="detail">
                        <div class="label">Gate</div>
                        <div class="value">A7</div>
                    </div>

                    <div class="detail">
                        <div class="label">Baggage</div>
                        <div class="value">{baggage}</div>
                    </div>

                    <div class="detail">
                        <div class="label">Phone</div>
                        <div class="value">{phone}</div>
                    </div>

                </div>

                <div class="barcode"></div>

            </div>

            <div class="tear"></div>

            <div class="footer">
                Demo boarding pass • Please arrive at the airport on time.
            </div>

        </div>
    </body>
    </html>
    """

    st.html(boarding_html)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"""
        <div style="text-align:center;padding:4px 0 18px;">
            <div style="width:58px;height:58px;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;border-radius:16px;background:linear-gradient(145deg,rgba(255,255,255,.16),rgba(255,255,255,.06));border:1px solid rgba(255,255,255,.16);font-size:30px;box-shadow:0 8px 20px rgba(0,0,0,.12);">✈️</div>
            <div style="font-size:25px;font-weight:800;letter-spacing:-.5px;color:#FFFFFF;">
                Parwaaz
            </div>
            <div style="font-size:18px;color:#E9D37A;margin-top:1px;">
                پرواز
            </div>
            <div style="font-size:11px;color:#D8E9DD;margin-top:5px;">
                Every journey begins here.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    language = st.selectbox(
        "Language / زبان",
        options=["English", "Urdu"],
        index=0 if st.session_state.language == "English" else 1,
        key="language_selector",
    )
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()

    page = st.radio(
        "Navigation",
        [
            "🏠 Home",
            "👤 Customer",
            "🧑‍💼 Staff",
            "🤖 AI Assistant",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown(
        """
        <div style="
            background:rgba(255,255,255,0.08);
            padding:15px;
            border-radius:14px;
        ">
            <div style="font-size:11px;color:#C9A227;">
                NEXT FLIGHT
            </div>
            <b>PK-301</b><br>
            Lahore → Dubai<br>
            <span style="font-size:12px;color:#D8E9DD;">
                09:30 PKT • Gate A7
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:25px;
            font-size:11px;
            color:#B9CFC0;
        ">
            🇵🇰 Made for Pakistani travellers
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HOME PAGE
# ============================================================

if page == "🏠 Home":

    show_hero()
    show_flight_strip()
    show_metric_cards()

    st.markdown(
        '<div class="section-title">Flight Overview</div>',
        unsafe_allow_html=True,
    )

    chart_col, info_col = st.columns([1.35, 1], gap="large")

    with chart_col:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        show_donut_chart()
        st.markdown('</div>', unsafe_allow_html=True)

    with info_col:
        st.markdown(
            """
            <div class="dashboard-card">
                <div class="dashboard-card-title">✈️ Flight Details</div>
                <div class="detail-grid">
                    <div class="detail-item"><div class="detail-label">Route</div><div class="detail-value">Lahore → Dubai</div></div>
                    <div class="detail-item"><div class="detail-label">Gate</div><div class="detail-value">A7</div></div>
                    <div class="detail-item"><div class="detail-label">Departure</div><div class="detail-value">09:30 PKT</div></div>
                    <div class="detail-item"><div class="detail-label">Aircraft</div><div class="detail-value">Parwaaz Demo Flight PK-301</div></div>
                    <div class="detail-item"><div class="detail-label">Flight Type</div><div class="detail-value">International</div></div>
                    <div class="detail-item"><div class="detail-label">Check-in</div><div class="detail-value">Opens 3 hrs before</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    show_seat_map()


# ============================================================
# CUSTOMER PAGE
# ============================================================

elif page == "👤 Customer":

    t = LANGUAGE_TEXT[st.session_state.language]
    direction = "rtl" if st.session_state.language == "Urdu" else "ltr"

    st.markdown(
        f'<div class="section-title" dir="{direction}">{t["customer"]}</div>',
        unsafe_allow_html=True,
    )

    tab_book, tab_cancel, tab_booking, tab_available = st.tabs(
        [
            f"🎟️ {t['book']}",
            f"❌ {t['cancel']}",
            f"🪪 {t['my_booking']}",
            f"💺 {t['available']}",
        ]
    )

    # --------------------------------------------------------
    # BOOK
    # --------------------------------------------------------

    with tab_book:

        st.markdown(
            f"""
            <div class="booking-intro-card" dir="{direction}">
                <h3>
                    {t['book_title']}
                </h3>
                <p>
                    Choose your flight, seat, and passenger details.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        available_seats = customer.view_available_seats()

        if not available_seats:

            st.warning("😔 Sorry, there are no available seats.")

        else:

            seat_options = {
                f'{seat["label"]} • {seat["class"]} • {money(seat["price"])}':
                seat["number"]
                for seat in available_seats
            }

            with st.form("booking_form"):

                flight_labels = {
                    f"{flight['flight']} • {flight['route']} • {flight['date']} • {flight['time']}": flight
                    for flight in FLIGHT_OPTIONS
                }

                selected_flight_label = st.selectbox(
                    t["flight"],
                    list(flight_labels.keys()),
                )
                selected_flight = flight_labels[selected_flight_label]

                passenger_name = st.text_input(
                    t["name"],
                    placeholder="e.g. Ahmad Khan",
                )

                passenger_phone = st.text_input(
                    t["phone"],
                    placeholder="+92 3XX XXXXXXX",
                    help="Format: +92 3XX XXXXXXX",
                )

                selected_seat = st.selectbox(
                    t["seat"],
                    list(seat_options.keys()),
                )

                selected_number = seat_options[selected_seat]

                st.info(
                    f"💰 Price: {money(get_seat_price(selected_number))} • "
                    f"✈️ {selected_flight['route']}"
                )

                payment_method = st.selectbox(
                    t["payment"],
                    [
                        "JazzCash",
                        "Easypaisa",
                        "Card",
                    ],
                )

                st.caption(
                    "Demo payment only — no real transaction will be processed."
                )

                submitted = st.form_submit_button(
                    f"✈️ {t['confirm']}",
                    width="stretch",
                )

                if submitted:

                    if not passenger_name.strip():

                        st.error("⚠️ Please enter the passenger name.")

                    elif not is_valid_pk_phone(passenger_phone):

                        st.error("⚠️ Please use the format +92 3XX XXXXXXX.")

                    else:

                        with st.spinner("Confirming your booking..."):

                            result = customer.book_seat(
                                passenger_name,
                                selected_number,
                            )

                        if result["success"]:

                            st.session_state.passenger_phones[
                                passenger_name.strip().lower()
                            ] = passenger_phone.strip()

                            result["phone"] = passenger_phone.strip()
                            result["flight"] = selected_flight
                            st.session_state.selected_flight = selected_flight
                            st.session_state.last_booking = result

                            add_activity(
                                f'{result["name"]} booked seat {result["label"]} on {selected_flight["flight"]}'
                            )

                            st.toast(
                                "Booking confirmed! ✈️",
                                icon="🎉",
                            )

                            st.balloons()

                            st.success(result["message"])

                        else:

                            st.error(result["message"])

            if st.session_state.last_booking:

                st.markdown(
                    '<div class="section-title">Your Boarding Pass</div>',
                    unsafe_allow_html=True,
                )

                show_boarding_pass(
                    st.session_state.last_booking
                )

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    with tab_cancel:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.subheader(t["cancel_title"])

        cancel_name = st.text_input(
            t["name"],
            key="cancel_name",
        )

        cancel_seat = st.number_input(
            "Seat Number",
            min_value=1,
            max_value=TOTAL_SEATS,
            step=1,
            key="cancel_seat",
        )

        if st.button(
            f"❌ {t['cancel']}",
            width="stretch",
        ):

            with st.spinner("Cancelling booking..."):

                result = customer.cancel_seat(
                    cancel_name,
                    cancel_seat,
                )

            if result["success"]:

                add_activity(
                    f"Booking cancelled for seat {result['label']}"
                )

                st.success(result["message"])

            else:

                st.error(result["message"])

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # MY BOOKING
    # --------------------------------------------------------

    with tab_booking:

        st.markdown(
            '<div class="card">',
            unsafe_allow_html=True,
        )

        st.subheader(t["my_booking"])

        search_name = st.text_input(
            t["name"],
            key="my_booking_name",
        )

        if st.button(
            f"🔎 {t['find']}",
            width="stretch",
        ):

            result = customer.view_booking(search_name)

            if result["success"]:

                st.success(result["message"])

                for booking in result["bookings"]:

                    show_boarding_pass(
                        {
                            "name": booking["name"],
                            "label": booking["label"],
                            "class": booking["class"],
                        }
                    )

            else:

                st.warning(result["message"])

        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # AVAILABLE SEATS
    # --------------------------------------------------------

    with tab_available:

        available = customer.view_available_seats()

        if available:

            df = pd.DataFrame(available)

            df = df.rename(
                columns={
                    "number": "Seat No.",
                    "label": "Seat",
                    "class": "Class",
                    "price": "Price (PKR)",
                }
            )

            st.dataframe(
                df[
                    [
                        "Seat No.",
                        "Seat",
                        "Class",
                        "Price (PKR)",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

        else:

            st.info("No seats are currently available.")


# ============================================================
# STAFF PAGE
# ============================================================

elif page == "🧑‍💼 Staff":

    st.markdown(
        '<div class="section-title">Staff Dashboard</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not st.session_state.staff_logged_in:

        st.markdown(
            """
            <div class="staff-login-card">
                <h3>
                    🔐 Staff Login
                </h3>
                <p>
                    Enter the staff password to access flight management.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        password = st.text_input(
            "Staff Password",
            type="password",
        )

        if st.button(
            "Login",
            width="stretch",
        ):

            if password == STAFF_PASSWORD:

                st.session_state.staff_logged_in = True
                st.success("Login successful.")
                st.rerun()

            else:

                st.error("Incorrect staff password.")

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    else:

        top_col1, top_col2 = st.columns([5, 1])

        with top_col1:

            st.success("🟢 Staff access active.")

        with top_col2:

            if st.button("Logout"):

                st.session_state.staff_logged_in = False
                st.rerun()

        show_metric_cards()

        st.markdown(
            '<div class="section-title">Flight Analytics</div>',
            unsafe_allow_html=True,
        )

        booked, available, occupancy = get_metrics()

        chart1, chart2 = st.columns(2)

        with chart1:

            fig = go.Figure(
                go.Bar(
                    x=["Booked", "Available"],
                    y=[booked, available],
                    text=[booked, available],
                    textposition="auto",
                    marker_color=[RED, GREEN],
                )
            )

            fig.update_layout(
                title="Seat Status",
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with chart2:

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=occupancy,
                    title={"text": "Occupancy %"},
                    gauge={
                        "axis": {
                            "range": [0, 100]
                        },
                        "bar": {
                            "color": DEEP_GREEN
                        },
                        "steps": [
                            {
                                "range": [0, 50],
                                "color": "#E8F2EA",
                            },
                            {
                                "range": [50, 100],
                                "color": "#D5E7D8",
                            },
                        ],
                    },
                )
            )

            fig.update_layout(
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        # ----------------------------------------------------
        # PASSENGERS
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Passenger List</div>',
            unsafe_allow_html=True,
        )

        passengers = staff.view_booked_passengers()

        if passengers:

            passenger_df = pd.DataFrame(passengers)

            passenger_df = passenger_df.rename(
                columns={
                    "seat": "Seat No.",
                    "seat_label": "Seat",
                    "passenger": "Passenger",
                    "class": "Class",
                    "price": "Price (PKR)",
                }
            )

            st.dataframe(
                passenger_df,
                width="stretch",
                hide_index=True,
            )

            csv_data = passenger_df.to_csv(index=False).encode(
                "utf-8"
            )

            st.download_button(
                "⬇️ Download Passenger CSV",
                data=csv_data,
                file_name="parwaaz_passengers.csv",
                mime="text/csv",
            )

        else:

            st.info("No passengers are currently booked.")

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Search Passenger</div>',
            unsafe_allow_html=True,
        )

        search = st.text_input(
            "Search passenger name",
            placeholder="e.g. Ahmad",
        )

        if search:

            results = staff.search_passenger(search)

            if results:

                st.dataframe(
                    pd.DataFrame(results),
                    width="stretch",
                    hide_index=True,
                )

            else:

                st.warning("No passenger found.")

        # ----------------------------------------------------
        # SEAT CHECKER
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Seat Checker</div>',
            unsafe_allow_html=True,
        )

        check_seat_number = st.number_input(
            "Seat number",
            min_value=1,
            max_value=TOTAL_SEATS,
            step=1,
        )

        if st.button("Check Seat"):

            result = staff.check_seat(
                check_seat_number
            )

            if result["status"] == "Booked":

                st.error(
                    f"🔴 {result['label']} is booked by "
                    f"{result['passenger']}."
                )

            else:

                st.success(
                    f"🟢 {result['label']} is available."
                )

        # ----------------------------------------------------
        # ACTIVITY LOG
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Recent Activity</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.activity_log:

            for activity in st.session_state.activity_log:

                st.markdown(
                    f"""
                    <div class="info-box">
                        <b>{activity["time"]}</b>
                        &nbsp; {html.escape(activity["action"])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.info("No recent activity.")

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Flight Management</div>',
            unsafe_allow_html=True,
        )

        reset_confirm = st.checkbox(
            "I understand that resetting will remove all bookings."
        )

        if reset_confirm:

            if st.button(
                "⚠️ Reset Flight",
                width="stretch",
            ):

                result = staff.reset_flight()

                st.session_state.last_booking = None
                st.session_state.activity_log = []

                st.success(result["message"])

                st.rerun()


# ============================================================
# AI ASSISTANT
# ============================================================

if page == "🤖 AI Assistant":
    st.markdown(
        """
        <div class="hero">
            <div class="hero-content">
                <div class="hero-kicker">PARWAAZ AI</div>
                <h1>Your Personal Flight Assistant</h1>
                <p>Ask about seats, bookings, cancellations, and fares.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not GROQ_API_KEY:
        st.warning(
            "AI Assistant is currently unavailable because the Groq API key "
            "has not been configured."
        )
        st.info(
            "Add GROQ_API_KEY to your .env file and restart Streamlit."
        )
        st.stop()

    # --------------------------------------------------------
    # Tool definitions
    # --------------------------------------------------------

    tools = [
        {
            "type": "function",
            "function": {
                "name": "view_available_seats",
                "description": (
                    "Show all currently available seats on the Parwaaz flight."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "book_seat",
                "description": (
                    "Book one available seat for a passenger. "
                    "The passenger name and seat number are required."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Passenger's full name.",
                        },
                        "seat": {
                            "type": "integer",
                            "description": (
                                "Seat number from 1 to 30. "
                                "For example, seat 3 means 3A."
                            ),
                        },
                    },
                    "required": ["name", "seat"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "cancel_seat",
                "description": (
                    "Cancel a passenger's booking. "
                    "The passenger name and seat number are required."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Passenger's full name.",
                        },
                        "seat": {
                            "type": "integer",
                            "description": "Seat number from 1 to 30.",
                        },
                    },
                    "required": ["name", "seat"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "view_booking",
                "description": (
                    "Find all bookings belonging to a passenger."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Passenger's full name.",
                        },
                    },
                    "required": ["name"],
                },
            },
        },
    ]

    # --------------------------------------------------------
    # Tool executor
    # --------------------------------------------------------

    def execute_ai_tool(tool_name, arguments):
        """
        Execute only approved Customer methods.

        The AI never edits passenger_names or seat_status directly.
        """

        try:
            if tool_name == "view_available_seats":
                result = customer.view_available_seats()

            elif tool_name == "book_seat":
                name = arguments.get("name", "").strip()
                seat = int(arguments.get("seat"))

                result = customer.book_seat(name, seat)

                if isinstance(result, dict) and result.get("success"):
                    add_activity(
                        f"AI booked seat {seat} for {name}"
                    )

            elif tool_name == "cancel_seat":
                name = arguments.get("name", "").strip()
                seat = int(arguments.get("seat"))

                result = customer.cancel_seat(name, seat)

                if isinstance(result, dict) and result.get("success"):
                    add_activity(
                        f"AI cancelled seat {seat} for {name}"
                    )

            elif tool_name == "view_booking":
                name = arguments.get("name", "").strip()
                result = customer.view_booking(name)

            else:
                result = "This action is not available."

            return result

        except Exception as error:
            return f"Unable to complete the requested action: {error}"

    # --------------------------------------------------------
    # Chat history
    # --------------------------------------------------------

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display previous messages
    for message in st.session_state.chat_messages:
        role = message.get("role")

        # Do not display internal tool messages
        if role == "tool":
            continue

        content = message.get("content")

        if content:
            with st.chat_message(
                "assistant" if role == "assistant" else "user"
            ):
                st.markdown(content)

    # --------------------------------------------------------
    # Helpful suggestions
    # --------------------------------------------------------

    st.markdown("### Try asking")

    suggestion_cols = st.columns(3)

    suggestions = [
        "Show available seats",
        "What is the price of business class?",
        "Mere liye available seats batao",
    ]

    for index, suggestion in enumerate(suggestions):
        with suggestion_cols[index]:
            if st.button(
                suggestion,
                key=f"ai_suggestion_{index}",
                width="stretch",
            ):
                st.session_state.ai_pending_message = suggestion
                st.rerun()

    # --------------------------------------------------------
    # User message
    # --------------------------------------------------------

    pending_message = st.session_state.pop(
        "ai_pending_message",
        None,
    )

    user_prompt = st.chat_input(
        "Ask Parwaaz AI..."
    )

    if pending_message:
        user_prompt = pending_message

    if user_prompt:

        # Add user message to history
        st.session_state.chat_messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_prompt)

        # ----------------------------------------------------
        # System instructions
        # ----------------------------------------------------

        available_seats = customer.view_available_seats()

        current_flight = st.session_state.selected_flight

        system_prompt = f"""
You are Parwaaz AI, the friendly airline reservation assistant
for Parwaaz (پرواز).

Your job is to help Pakistani passengers with flight reservations.

CURRENT DEMO FLIGHT
Route: {current_flight['route']}
Flight: {current_flight['flight']}
Date: {current_flight['date']}
Departure: {current_flight['time']}
Gate: {current_flight['gate']}

PRICES
Business Class: Rs. 95,000
Economy Class: Rs. 38,000

SEAT RULES
- Seats 1-12 are Business Class.
- Seats 13-30 are Economy Class.
- Seat numbers are 1 to 30.
- Never invent seat availability.
- Always use the view_available_seats tool when the user asks
  about currently available seats.
- Always use the booking tools when changing a reservation.
- Never claim that a booking or cancellation succeeded unless
  the tool result confirms it.

AVAILABLE SEATS RIGHT NOW
{available_seats}

IMPORTANT
- You understand English and Roman Urdu.
- Reply in the same language/style as the user when practical.
- Keep answers friendly and concise.
- Never ask for CNIC or any government ID number.
- Do not claim that real payment has been processed.
- JazzCash, Easypaisa and Card are visual/demo payment methods only.
- You are allowed to use ONLY these reservation tools:
  view_available_seats
  book_seat
  cancel_seat
  view_booking
- Never directly modify passenger_names or seat_status.
- Never invent a booking reference.
"""

        # ----------------------------------------------------
        # Send request to Groq
        # ----------------------------------------------------

        client = Groq(api_key=GROQ_API_KEY)

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # Add conversation history
        messages.extend(
            st.session_state.chat_messages
        )

        try:
            with st.spinner("Parwaaz AI is thinking..."):

                # First model call
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2,
                    max_completion_tokens=800,
                )

                assistant_message = response.choices[0].message

                # ------------------------------------------------
                # Process tool calls
                # ------------------------------------------------

                if assistant_message.tool_calls:

                    # Add assistant tool-call message
                    messages.append(assistant_message)

                    for tool_call in assistant_message.tool_calls:

                        tool_name = tool_call.function.name

                        arguments = json.loads(
                            tool_call.function.arguments
                        )

                        tool_result = execute_ai_tool(
                            tool_name,
                            arguments,
                        )

                        # Send tool result back to model
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": json.dumps(
                                    tool_result,
                                    default=str,
                                ),
                            }
                        )

                    # --------------------------------------------
                    # Final response after tool execution
                    # --------------------------------------------

                    final_response = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=messages,
                        tools=tools,
                        tool_choice="none",
                        temperature=0.2,
                        max_completion_tokens=800,
                    )

                    assistant_text = (
                        final_response.choices[0].message.content
                    )

                else:
                    assistant_text = assistant_message.content

                if not assistant_text:
                    assistant_text = (
                        "I couldn't generate a response. "
                        "Please try again."
                    )

                # Save final assistant response
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_text,
                    }
                )

                # Show final response
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)

                # Refresh UI after a booking/cancellation
                st.rerun()

        except Exception as error:
            st.error(
                f"AI Assistant error: {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🇵🇰 Parwaaz • پرواز &nbsp; | &nbsp;
        Built with Python, Streamlit and Groq
        <br>
        Every journey begins here.
    </div>
    """,
    unsafe_allow_html=True,
)