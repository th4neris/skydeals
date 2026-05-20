import streamlit as st
import sqlite3
import re
from scrapers.expedia.expedia_return import scrape_lowest_price_return
from scrapers.expedia.expediaoneway import scrape_lowest_price_one_way
from sendemail import send_email


st.set_page_config(
    page_title="SkyDeals",
    page_icon="SkyDeals",
    layout="wide"
)


def get_tracking_history():
    connection = sqlite3.connect("skydeals.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, email, origin, destination, cabin_class,
               adults, children, infants_lap, infants_seat,
               children_ages, infants_lap_ages, infants_seat_ages,
               travel_date, return_date, target_price, trip_type
        FROM flight_tracks_return
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    connection.close()
    return rows


def init_database():
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER,
        price INTEGER,
        checked_at TEXT,
        FOREIGN KEY(flight_id) REFERENCES flight_tracks_return(id)
    )
    """)

    cursor.execute("SELECT * FROM airports")
    codes = cursor.fetchall()
    airport_codes = sorted(list(set(code[1] for code in codes)))

    connection.commit()
    connection.close()

    return airport_codes


def save_flight(data):
    connection = sqlite3.connect("skydeals.db")
    cursor = connection.cursor()

    cursor.execute("""
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
        data["email"], data["origin"], data["destination"], data["cabin_class"],
        data["adults"], data["children"], data["infants_lap"], data["infants_seat"],
        data["children_ages_str"], data["infants_lap_str"], data["infants_seat_str"],
        str(data["travel_date"]), str(data["return_date"]) if data["return_date"] else None,
        data["target"], data["trip_type"]
    ))

    existing_flight = cursor.fetchone()

    if existing_flight:
        connection.close()
        return False

    cursor.execute("""
        INSERT INTO flight_tracks_return (
            email, origin, destination, cabin_class, adults, children,
            infants_lap, infants_seat, children_ages, infants_lap_ages,
            infants_seat_ages, travel_date, return_date, target_price, trip_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["email"], data["origin"], data["destination"], data["cabin_class"],
        data["adults"], data["children"], data["infants_lap"], data["infants_seat"],
        data["children_ages_str"], data["infants_lap_str"], data["infants_seat_str"],
        str(data["travel_date"]), str(data["return_date"]) if data["return_date"] else None,
        data["target"], data["trip_type"]
    ))

    connection.commit()
    connection.close()
    return True


def delete_flight(flight_id):
    connection = sqlite3.connect("skydeals.db")
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM flight_tracks_return
        WHERE id = ?
    """, (flight_id,))

    connection.commit()
    connection.close()


def convert_ages(text):
    if not text:
        return []

    return [int(age) for age in text.split(",") if age]


def extract_price_number(price):
    return int(re.sub(r"[^\d]", "", price))


def run_scraper(data):
    if data["trip_type"] == "Return":
        return scrape_lowest_price_return(
            adults=data["adults"],
            children=data["children"],
            infants_lap=data["infants_lap"],
            infants_seat=data["infants_seat"],
            origin=data["origin"],
            destination=data["destination"],
            cabin_class=data["cabin_class"],
            travel_date=data["travel_date"],
            infants_lap_ages=data["infants_lap_ages"],
            infants_seat_ages=data["infants_seat_ages"],
            children_ages=data["children_ages"],
            return_date=data["return_date"]
        )

    return scrape_lowest_price_one_way(
        adults=data["adults"],
        children=data["children"],
        infants_lap=data["infants_lap"],
        infants_seat=data["infants_seat"],
        origin=data["origin"],
        destination=data["destination"],
        cabin_class=data["cabin_class"],
        travel_date=data["travel_date"],
        infants_lap_ages=data["infants_lap_ages"],
        infants_seat_ages=data["infants_seat_ages"],
        children_ages=data["children_ages"]
    )


def handle_price_result(price, target, email, origin, destination):
    if price is None:
        st.error("No flights found.")
        return

    price_number = extract_price_number(price)

    if price_number <= target:
        send_email(email, price, origin=origin, destination=destination)
        st.success("Price found under your target. Email sent.")
    else:
        st.warning("Price is higher than your target. No email sent.")


def collect_flight_info(airport_codes, trip_type):
    with st.container(border=True):
        st.subheader("Flight details")
        st.caption("Enter your route, passengers, dates, email and target price.")

        route_col1, route_col2, route_col3 = st.columns(3)

        with route_col1:
            origin = st.selectbox("From", airport_codes, key=f"origin_{trip_type}")

        with route_col2:
            destination = st.selectbox("To", airport_codes, key=f"destination_{trip_type}")

        with route_col3:
            cabin_class = st.selectbox(
                "Cabin class",
                ["Economy", "Premium economy", "Business class", "First class"],
                key=f"cabin_{trip_type}"
            )

        st.divider()

        passenger_col1, passenger_col2, passenger_col3, passenger_col4 = st.columns(4)

        with passenger_col1:
            adults = st.number_input(
                "Adults",
                min_value=1,
                max_value=9,
                key=f"adults_{trip_type}"
            )

        with passenger_col2:
            children = st.number_input(
                "Children",
                min_value=0,
                max_value=8,
                key=f"children_{trip_type}"
            )

        with passenger_col3:
            infants_lap = st.number_input(
                "Infants on lap",
                min_value=0,
                max_value=4,
                key=f"infants_lap_{trip_type}"
            )

        with passenger_col4:
            infants_seat = st.number_input(
                "Infants on seat",
                min_value=0,
                max_value=6,
                key=f"infants_seat_{trip_type}"
            )

        children_ages = []
        infants_lap_ages = []
        infants_seat_ages = []

        if children > 0:
            st.write("Children ages")
            child_cols = st.columns(min(children, 4))

            for i in range(children):
                with child_cols[i % 4]:
                    age = st.selectbox(
                        f"Child {i + 1}",
                        list(range(2, 18)),
                        key=f"child_age_{trip_type}_{i}"
                    )
                    children_ages.append(age)

        if infants_lap > 0:
            st.write("Infants on lap ages")
            infant_lap_cols = st.columns(min(infants_lap, 4))

            for i in range(infants_lap):
                with infant_lap_cols[i % 4]:
                    age = st.selectbox(
                        f"Lap infant {i + 1}",
                        [0, 1],
                        key=f"infant_lap_age_{trip_type}_{i}"
                    )
                    infants_lap_ages.append(age)

        if infants_seat > 0:
            st.write("Infants on seat ages")
            infant_seat_cols = st.columns(min(infants_seat, 4))

            for i in range(infants_seat):
                with infant_seat_cols[i % 4]:
                    age = st.selectbox(
                        f"Seat infant {i + 1}",
                        [0, 1],
                        key=f"infant_seat_age_{trip_type}_{i}"
                    )
                    infants_seat_ages.append(age)

        st.divider()

        if trip_type == "Return":
            date_col1, date_col2, date_col3 = st.columns(3)

            with date_col1:
                travel_date = st.date_input("Departure date", key=f"travel_date_{trip_type}")

            with date_col2:
                return_date = st.date_input("Return date", key=f"return_date_{trip_type}")

            with date_col3:
                target = st.number_input("Target price", min_value=0, key=f"target_{trip_type}")

        else:
            date_col1, date_col2 = st.columns(2)

            with date_col1:
                travel_date = st.date_input("Departure date", key=f"travel_date_{trip_type}")

            with date_col2:
                target = st.number_input("Target price", min_value=0, key=f"target_{trip_type}")

            return_date = None

        email = st.text_input("Email", key=f"email_{trip_type}")

    return {
        "origin": origin,
        "destination": destination,
        "cabin_class": cabin_class,
        "adults": adults,
        "children": children,
        "infants_lap": infants_lap,
        "infants_seat": infants_seat,
        "children_ages": children_ages,
        "infants_lap_ages": infants_lap_ages,
        "infants_seat_ages": infants_seat_ages,
        "children_ages_str": ",".join(map(str, children_ages)) if children_ages else "",
        "infants_lap_str": ",".join(map(str, infants_lap_ages)) if infants_lap_ages else "",
        "infants_seat_str": ",".join(map(str, infants_seat_ages)) if infants_seat_ages else "",
        "travel_date": travel_date,
        "return_date": return_date,
        "email": email,
        "target": target,
        "trip_type": trip_type
    }


airport_codes = init_database()

if "trip_type" not in st.session_state:
    st.session_state.trip_type = None


st.title("SkyDeals")
st.caption("Track flight prices and get notified when prices drop below your target.")

st.divider()

st.subheader("Choose your trip type")

trip_col1, trip_col2, trip_col3 = st.columns([1, 1, 4])

with trip_col1:
    if st.button("Return", use_container_width=True):
        st.session_state.trip_type = "Return"

with trip_col2:
    if st.button("One way", use_container_width=True):
        st.session_state.trip_type = "One way"

if st.session_state.trip_type:
    st.info(f"Selected trip type: {st.session_state.trip_type}")

    flight_data = collect_flight_info(airport_codes, st.session_state.trip_type)

    total_travellers = (
        flight_data["adults"]
        + flight_data["children"]
        + flight_data["infants_lap"]
        + flight_data["infants_seat"]
    )

    total_infants = flight_data["infants_lap"] + flight_data["infants_seat"]
    infant_condition = total_infants <= 2 * flight_data["adults"]

    if total_travellers > 10:
        st.error("Only 10 travellers are allowed.")

    if not infant_condition:
        st.error("Each adult can accompany at most 2 infants.")

    search_clicked = st.button(
        "Start searching",
        type="primary",
        use_container_width=True
    )

    if search_clicked:
        if total_travellers > 10:
            st.error("Only 10 travellers are allowed.")
        elif not infant_condition:
            st.error("Each adult can accompany at most 2 infants.")
        elif not flight_data["email"]:
            st.error("Please enter an email address.")
        else:
            saved = save_flight(flight_data)

            if saved:
                st.success("Flight added to your tracking list.")
                with st.spinner("Searching for the lowest price..."):
                    price = run_scraper(flight_data)

                handle_price_result(
                    price,
                    flight_data["target"],
                    flight_data["email"],
                    flight_data["origin"],
                    flight_data["destination"]
                )
            else:
                st.warning("This flight is already being tracked. Use Re-track from Active Price Tracks.")

st.divider()

st.subheader("Active Price Tracks")
st.caption("Manage your saved flight searches.")

history_data = get_tracking_history()

if not history_data:
    st.info("You are not tracking any flights yet.")
else:
    for row in history_data:
        flight = {
            "ID": row[0],
            "Email": row[1],
            "From": row[2],
            "To": row[3],
            "Class": row[4],
            "Adults": row[5],
            "Children": row[6],
            "Infants Lap": row[7],
            "Infants Seat": row[8],
            "Children Ages": row[9],
            "Infants Lap Ages": row[10],
            "Infants Seat Ages": row[11],
            "Departure Date": row[12],
            "Return Date": row[13] if row[13] else "N/A",
            "Target Price": row[14],
            "Trip Type": row[15]
        }

        with st.container(border=True):
            main_col, action_col = st.columns([4, 1])

            with main_col:
                st.markdown(f"### {flight['From']} to {flight['To']}")

                metric_col1, metric_col2, metric_col3 = st.columns(3)

                with metric_col1:
                    st.metric("Trip", flight["Trip Type"])

                with metric_col2:
                    st.metric("Class", flight["Class"])

                with metric_col3:
                    st.metric("Target", f"{flight['Target Price']}€")

                date_col1, date_col2 = st.columns(2)

                with date_col1:
                    st.write(f"Departure: {flight['Departure Date']}")

                with date_col2:
                    if flight["Return Date"] != "N/A":
                        st.write(f"Return: {flight['Return Date']}")
                    else:
                        st.write("Return: N/A")

                passenger_col1, passenger_col2, passenger_col3, passenger_col4 = st.columns(4)

                with passenger_col1:
                    st.write(f"Adults: {flight['Adults']}")

                with passenger_col2:
                    st.write(f"Children: {flight['Children']}")

                with passenger_col3:
                    st.write(f"Lap infants: {flight['Infants Lap']}")

                with passenger_col4:
                    st.write(f"Seat infants: {flight['Infants Seat']}")

            with action_col:
                st.write("")
                st.write("")

                retrack = st.button(
                    "Re-track",
                    key=f"retrack_{flight['ID']}",
                    type="primary",
                    use_container_width=True
                )

                delete = st.button(
                    "Delete",
                    key=f"delete_{flight['ID']}",
                    use_container_width=True
                )

        if delete:
            delete_flight(flight["ID"])
            st.success("Flight deleted.")
            st.rerun()

        if retrack:
            retrack_data = {
                "origin": flight["From"],
                "destination": flight["To"],
                "cabin_class": flight["Class"],
                "adults": flight["Adults"],
                "children": flight["Children"],
                "infants_lap": flight["Infants Lap"],
                "infants_seat": flight["Infants Seat"],
                "children_ages": convert_ages(flight["Children Ages"]),
                "infants_lap_ages": convert_ages(flight["Infants Lap Ages"]),
                "infants_seat_ages": convert_ages(flight["Infants Seat Ages"]),
                "travel_date": flight["Departure Date"],
                "return_date": None if flight["Return Date"] == "N/A" else flight["Return Date"],
                "target": flight["Target Price"],
                "email": flight["Email"],
                "trip_type": flight["Trip Type"]
            }

            with st.spinner("Re-tracking this flight..."):
                price = run_scraper(retrack_data)

            handle_price_result(
                price,
                retrack_data["target"],
                retrack_data["email"],
                retrack_data["origin"],
                retrack_data["destination"]
            )