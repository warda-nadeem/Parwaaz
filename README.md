# ✈️ Parwaaz — Airline Reservation System

> **Every journey begins here.**

Parwaaz (پرواز) is a modern airline reservation and flight management web application built with **Python and Streamlit**. It provides a simple and professional interface for customers to view flights, select seats, make bookings, manage reservations, and interact with an AI assistant.

The application is designed with Pakistani users in mind, using **PKR currency**, Pakistani routes, and English/Roman Urdu AI interaction.

---

## 🌟 Features

### 👤 Customer Features

- ✈️ View available flights
- 🪑 Interactive seat selection
- 🎫 Book flight seats
- ❌ Cancel bookings
- 🔎 View booking information
- 💺 Check available seats
- 👥 Maximum of 3 seats per customer
- 💰 Economy and Business class pricing
- 🧳 Baggage allowance information
- 🎟️ Digital boarding pass
- 📱 Pakistani phone number format

---

## 🤖 AI Travel Assistant

Parwaaz includes an AI-powered travel assistant that can understand:

- English
- Roman Urdu

The AI assistant can help customers with:

- Checking available seats
- Booking seats
- Cancelling seats
- Viewing booking information
- Answering basic flight-related questions

The AI assistant is powered by **Groq**.

---

## 👨‍💼 Staff Dashboard

Staff members can access additional flight-management features through a password-protected staff area.

Staff features include:

- 👀 View all seats
- 👥 View booked passengers
- 🔍 Search passengers
- 💺 Check individual seat status
- 📊 Count available seats
- 🔄 Reset flight
- 📈 View booking activity
- 📥 Download booking information as CSV

---

## 💺 Seat System

Parwaaz provides **30 seats** divided into:

| Class | Rows | Seats |
|---|---|---|
| Business | 1–2 | A, B, C, D, E, F |
| Economy | 3–5 | A, B, C, D, E, F |

Each seat can be:

- Available
- Booked

The system prevents double booking of the same seat.

---

## 💰 Ticket Prices

| Class | Price |
|---|---:|
| Economy | Rs. 38,000 |
| Business | Rs. 95,000 |

All prices are displayed in **Pakistani Rupees (PKR)**.

---

## ✈️ Sample Flight Routes

The application includes sample routes such as:

- Lahore → Karachi
- Islamabad → Dubai
- Karachi → Jeddah
- Peshawar → Doha
- Multan → Islamabad

Flight times are displayed in **Pakistan Standard Time (PKT)**.

---

## 💳 Payment Methods

The application includes visual/mock payment options:

- JazzCash
- Easypaisa
- Card

> **Note:** These are demonstration payment options only. No real payment is processed.

---

## 🌐 Language Support

Parwaaz provides a language selector for:

- 🇬🇧 English
- 🇵🇰 Urdu

The AI assistant can also understand **Roman Urdu**.

---

## 🎨 User Interface

The application uses a professional airline-inspired design with:

- Deep green theme
- White cards
- Soft gold accents
- Responsive layouts
- Flight information cards
- Interactive seat map
- Boarding pass design
- AI assistant interface
- Customer and staff sections

---

## 🛠️ Technologies Used

- **Python**
- **Streamlit**
- **Plotly**
- **Groq API**
- **python-dotenv**

---

## 📁 Project Structure

```text
Parwaaz/
│
├── app.py
├── reservation.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env
