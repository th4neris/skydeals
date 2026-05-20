import streamlit as st
import sqlite3
from scrapers.expedia.expedia_return import scrape_lowest_price_return
from scrapers.expedia.expediaoneway import  scrape_lowest_price_one_way
from sendemail import send_email
import re

def get_tracking_history():
    """Fetches all tracked flights from the database and returns them as a clean DataFrame or list."""
    connection = sqlite3.connect("skydeals.db")
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, origin, destination, trip_type, travel_date, return_date, cabin_class, target_price 
        FROM flight_tracks_return
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    connection.close()
    return rows


connection = sqlite3.connect("skydeals.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS flight_tracks_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    cabin_class TEXT NOT NULL,
    adults INTEGER NOT NULL,
    children INTEGER NOT NULL,
    infants_lap INTEGER NOT NULL,
    infants_seat INTEGER NOT NULL,
    children_ages TEXT,      
    infants_lap_ages TEXT,   
    infants_seat_ages TEXT,  
    travel_date TEXT NOT NULL,
    return_date TEXT,        
    target_price INTEGER NOT NULL,
    trip_type TEXT NOT NULL  
)
""")
connection.commit()
cursor.execute("SELECT * FROM airports")
codes = cursor.fetchall()
airport_codes = sorted(list(set(code[1] for code in codes)))
connection.close()

if "infants_lap" not in st.session_state:
    st.session_state.infants_lap = 0

if "infants_seat" not in st.session_state:
    st.session_state.infants_seat = 0

st.title("Welcome to SkyDeals, find the cheapest price for your next flight!")
st.subheader("Choose your trip type!")
if "trip_type" not in st.session_state:
    st.session_state.trip_type = "None"

with st.container(horizontal=True):
    if st.button("Return"):
        st.session_state.trip_type = "Return"

    if st.button("One way"):
        st.session_state.trip_type = "One way"
if st.session_state.trip_type == "Return":
    with st.container(border=True):
        st.write("Fill out the necessary informations about your flight!")

        origin = st.selectbox("From",
                            airport_codes)
        destination =st.selectbox("To",
                            airport_codes)
        cabin_class = st.selectbox("Cabin class",
                                ['Economy', 'Premium economy', 'Business class', 'First class'])
        with st.container(border=False, horizontal=True):
            adults = st.number_input("How many adults\n", min_value=1, max_value=9)
            children =st.number_input("Children (2 to 17)\n", min_value=0, max_value=8)
            infants_lap = st.number_input("Infants on lap? (<2)\n", min_value=0, max_value=4,  key="infants_lap",
            disabled=st.session_state["infants_seat"] > 0)
            infants_seat = st.number_input("Infants on seat? (<2)?\n", min_value=0, max_value=6,  key="infants_seat",
            disabled=st.session_state["infants_lap"] > 0)
            children_ages = []
            infants_lap_ages = []
            infants_seat_ages = []

        if children > 0:
            st.write("Children ages")
            for i in range(children):
                age = st.selectbox(
                    f"Child {i+1} age",
                    list(range(2, 18)),
                    key=f"child_age_{i}"
                )
                children_ages.append(age)

        if infants_lap > 0:
            st.write("Infants on lap ages")
            for i in range(infants_lap):
                age = st.selectbox(
                    f"Infant on lap {i+1} age",
                    [0, 1],
                    key=f"infant_lap_age_{i}"
                )
                infants_lap_ages.append(age)
            
            
        if infants_seat > 0:
            st.write("Infants in seat ages")
            for i in range(infants_seat):
                age = st.selectbox(
                    f"Infant in seat {i+1} age",
                    [0, 1],
                    key=f"infant_seat_age_{i}"
                )
                infants_seat_ages.append(age)
                
        travel_date = st.date_input("When are you travelling?")
        return_date = st.date_input("Return date?")
        email = st.text_input("Email:")
        target = st.number_input("Notify me when price is under:", min_value=0)
    total_infants = infants_lap+infants_seat
    
    scrape = st.button("Start searching!")
    total = adults+children+infants_lap+infants_seat
    if total > 10:
        st.error("Only 10 are travellers allowed!")
    if scrape:
        if total > 10:
            st.error("Only 10 travellers are allowed!")
        else:
            children_ages_str = ",".join(map(str, children_ages)) if children_ages else ""
            infants_lap_str = ",".join(map(str, infants_lap_ages)) if infants_lap_ages else ""
            infants_seat_str = ",".join(map(str, infants_seat_ages)) if infants_seat_ages else ""

            conn = sqlite3.connect("skydeals.db")
            db_cursor = conn.cursor()
            db_cursor.execute("""
                SELECT id FROM flight_tracks_return
                WHERE email = ?
                AND origin = ?
                AND destination = ?
                AND cabin_class = ?
                AND adults = ?
                AND children = ?
                AND infants_lap = ?
                AND infants_seat = ?
                AND children_ages = ?
                AND infants_lap_ages = ?
                AND infants_seat_ages = ?
                AND travel_date = ?
                AND return_date IS ?
                AND target_price = ?
                AND trip_type = ?
            """, (
                email, origin, destination, cabin_class, adults, children,
                infants_lap, infants_seat, children_ages_str, infants_lap_str,
                infants_seat_str, str(travel_date), str(return_date), target, "Return"
            ))
            existing_flight = db_cursor.fetchone()
            if existing_flight:
                st.warning("This flight is already in your tracking list.")
            else:
                
                db_cursor.execute("""
                    INSERT INTO flight_tracks_return (
                        email, origin, destination, cabin_class, adults, children, 
                        infants_lap, infants_seat, children_ages, infants_lap_ages, 
                        infants_seat_ages, travel_date, return_date, target_price, trip_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email, origin, destination, cabin_class, adults, children,
                    infants_lap, infants_seat, children_ages_str, infants_lap_str,
                    infants_seat_str, str(travel_date), str(return_date), target, "Return"
                ))
                conn.commit()
                st.success("Flight added to your tracking list!")
            conn.close()
            
           
            price = scrape_lowest_price_return(
                adults=adults,
                children=children,
                infants_lap=infants_lap,
                infants_seat=infants_seat,
                origin=origin,
                destination=destination,
                cabin_class=cabin_class,
                travel_date=travel_date,
                infants_lap_ages=infants_lap_ages,
                infants_seat_ages=infants_seat_ages,
                children_ages=children_ages,
                return_date=return_date
            )

            if price is None:
                st.error("No flights found.")
            else:
                price_number = int(re.sub(r"[^\d]", "", price))
                if price_number <= target:
                    send_email(email, price, origin=origin, destination=destination)
                    st.info("Email sent! (don't forget to check spam too)")
                else:
                    st.warning("Price is higher than your target. No email sent.")

if st.session_state.trip_type == "One way":
    with st.container(border=True):
        st.write("Fill out the necessary informations about your flight!")

        origin = st.selectbox("From",
                            airport_codes)
        destination =st.selectbox("To",
                            airport_codes)
        cabin_class = st.selectbox("Cabin class",
                                ['Economy', 'Premium economy', 'Business class', 'First class'])
        with st.container(border=False, horizontal=True):
            adults = st.number_input("How many adults\n", min_value=1, max_value=9)
            children =st.number_input("Children (2 to 17)\n", min_value=0, max_value=8)
            infants_lap = st.number_input("Infants on lap? (<2)\n", min_value=0, max_value=4,  key="infants_lap",
            disabled=st.session_state["infants_seat"] > 0)
            infants_seat = st.number_input("Infants on seat? (<2)?\n", min_value=0, max_value=6,  key="infants_seat",
            disabled=st.session_state["infants_lap"] > 0)
            children_ages = []
            infants_lap_ages = []
            infants_seat_ages = []

        if children > 0:
            st.write("Children ages")
            for i in range(children):
                age = st.selectbox(
                    f"Child {i+1} age",
                    list(range(2, 18)),
                    key=f"child_age_{i}"
                )
                children_ages.append(age)

        if infants_lap > 0:
            st.write("Infants on lap ages")
            for i in range(infants_lap):
                age = st.selectbox(
                    f"Infant on lap {i+1} age",
                    [0, 1],
                    key=f"infant_lap_age_{i}"
                )
                infants_lap_ages.append(age)
            
            
        if infants_seat > 0:
            st.write("Infants in seat ages")
            for i in range(infants_seat):
                age = st.selectbox(
                    f"Infant in seat {i+1} age",
                    [0, 1],
                    key=f"infant_seat_age_{i}"
                )
                infants_seat_ages.append(age)
                
        travel_date = st.date_input("When are you travelling?")
        email = st.text_input("Email")
        target = st.number_input("Notify me when price is under:", min_value=0)
    scrape = st.button("Start searching!")
    total = adults+children+infants_lap+infants_seat
    total_infants = infants_lap + infants_seat
    condition = total_infants <= 2 * adults
    if total > 10:
        st.error("Only 10 are travellers allowed!")
    if scrape:
        if total > 10:
            st.error("Only 10 travellers are allowed!")
        elif not condition:
            st.error("Each adult can accompany at most 2 infants.")

        else:
            conn = sqlite3.connect("skydeals.db")
            db_cursor = conn.cursor()
            db_cursor.execute("""
                INSERT INTO flight_tracks_return (
                    email, origin, destination, cabin_class, adults, children, 
                    infants_lap, infants_seat, children_ages, infants_lap_ages, 
                    infants_seat_ages, travel_date, return_date, target_price, trip_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email, origin, destination, cabin_class, adults, children,
                infants_lap, infants_seat, children_ages_str, infants_lap_str,
                infants_seat_str, str(travel_date), None, target, "One way"
            ))
            conn.commit()
            conn.close()
            
            st.success("Flight added to your tracking list!")
            price = scrape_lowest_price_one_way(
                adults=adults,
                children=children,
                infants_lap=infants_lap,
                infants_seat=infants_seat,
                origin=origin,
                destination=destination,
                cabin_class=cabin_class,
                travel_date=travel_date,
                infants_lap_ages=infants_lap_ages,
                infants_seat_ages=infants_seat_ages,
                children_ages=children_ages,
            )
            if price is None:
                st.error("No flights found.")
            else:
                price_number = int(re.sub(r"[^\d]", "", price))
                if price_number <= target:
                    send_email(email, price, origin=origin, destination=destination)
                    st.info("Email sent! (don't forget to check spam too)")
                else:
                    st.warning("Price is higher than your target. No email sent.")

st.subheader("Your Active Price Tracks")

history_data = get_tracking_history()

if not history_data:
    st.info("You aren't tracking any flights yet. Use the forms above to start tracking!")
else:

    formatted_history = []
    for row in history_data:
        formatted_history.append({
            "ID": row[0],
            "From": row[1],
            "To": row[2],
            "Trip Type": row[3],
            "Departure Date": row[4],
            "Return Date": row[5] if row[5] else "N/A",
            "Class": row[6],
            "Target Price": f"{row[7]}" 
        })
    
    for flight in formatted_history:
        
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"### ✈️ {flight['From']} → {flight['To']}")
                st.write(f"{flight['Trip Type']} | {flight['Class']}")
                st.write(f"Departure: {flight['Departure Date']}")

                if flight["Return Date"] != "N/A":
                    st.write(f"Return: {flight['Return Date']}")

                st.write(f"Target price: under {flight['Target Price']}€")

            with col2:
                st.write("")
                st.write("")
                delete = st.button(
                    "Delete",
                    key=f"delete_{flight['ID']}"
                )
                retrack = st.button(
                    "Re-Track",
                    key=f"retrack_{flight['ID']}"
                )
            
        if delete:
            connection2 = sqlite3.connect("skydeals.db")
            cursor2 = connection2.cursor()
            cursor2.execute("""
                DELETE FROM flight_tracks_return
                WHERE id = ?
            """, (flight["ID"],))

            connection2.commit()
            connection2.close()

            st.success("Flight deleted.")
            st.rerun()
        if retrack:
            price = scrape_lowest_price_return(
                adults=adults,
                children=children,
                infants_lap=infants_lap,
                infants_seat=infants_seat,
                origin=origin,
                destination=destination,
                cabin_class=cabin_class,
                travel_date=travel_date,
                infants_lap_ages=infants_lap_ages,
                infants_seat_ages=infants_seat_ages,
                children_ages=children_ages,
                return_date=return_date
            )

            if price is None:
                st.error("No flights found.")
            else:
                price_number = int(re.sub(r"[^\d]", "", price))
                if price_number <= target:
                    send_email(email, price, origin=origin, destination=destination)
                    st.info("Email sent! (don't forget to check spam too)")
                else:
                    st.warning("Price is higher than your target. No email sent.")
            
