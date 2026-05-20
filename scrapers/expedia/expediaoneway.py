import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.webdriver.support.ui import Select
def scrape_lowest_price_one_way(origin, destination, travel_date, adults, children, infants_lap, infants_seat, cabin_class, children_ages, infants_lap_ages, infants_seat_ages):
    
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    time.sleep(3)
    wait = WebDriverWait(driver, 15)
    url = "https://euro.expedia.net/Flights?locale=en_IE&siteid=4400&semcid=EU.B.GOOGLE.BT-c-EN.FLIGHT&semdtl=a118255096713.b1185988509887.g1aud-2067245471241:kwd-44236943.e1c.m1Cj0KCQjwiJvQBhCYARIsAMjts3I4RQ8xfOeNCbzRir4QW5dVZ3uEQE4wA5bYiGYJEJeUDXE7krXxhy4aAq7WEALw_wcB.r1.c1.j19073701.k1.d1768103371974.h1e.i1.l1.n1.o1.p1.q1.s1expedia%20flights.t1.x1.f1.u1.v1.w1&gad_source=1&gad_campaignid=18255096713&gbraid=0AAAAACTxZ9bFh2fFzfM4QZj5R77e4azra&gclid=Cj0KCQjwiJvQBhCYARIsAMjts3I4RQ8xfOeNCbzRir4QW5dVZ3uEQE4wA5bYiGYJEJeUDXE7krXxhy4aAq7WEALw_wcB"
    driver.get(url)
    
    one_way_button = wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='One-way']")))
    one_way_button.click()
    time.sleep(1)
    origin_picker = wait.until(
    EC.element_to_be_clickable((By.ID, "origin_select-input"))
)

    driver.execute_script("arguments[0].click();", origin_picker)
    
    origin_picker.clear()
    origin_picker.send_keys(origin)
    result_origin = wait.until(EC.element_to_be_clickable(
    (By.CSS_SELECTOR,
    '[data-stid="origin_select-result-item-button"]'
    )))
    result_origin.click()

    destination_picker = wait.until(EC.visibility_of_element_located
                           ((By.ID, "destination_select-input")))
    time.sleep(1)
    destination_picker.click()
    
    destination_picker.clear()
    destination_picker.send_keys(destination)
    result_destination = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR,
        '[data-stid="destination_select-result-item-button"]'
    )))
    result_destination.click()

    expedia_date = travel_date.strftime("%Y-%m-%d")

    date_button = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-testid="uitk-date-selector-input1-default"]')
    )
    )   

    if date_button.get_attribute("aria-expanded") != "true":
        driver.execute_script("arguments[0].click();", date_button)

    going_day_number = str(travel_date.day)

    going_day = wait.until(
        EC.element_to_be_clickable(
        (
            By.XPATH,
            f"//div[contains(@class,'uitk-day-button') and contains(@class,'uitk-day-clickable') and normalize-space()='{going_day_number}']"
        )
    )
)

    driver.execute_script("arguments[0].click();", going_day)
    

    done_button = wait.until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                '[data-stid="apply-date-selector"]'
        )
    )
)

    driver.execute_script(
    "arguments[0].scrollIntoView({block:'center'});",
    done_button
    )

    driver.execute_script(
        "arguments[0].click();",
        done_button
)

    traveller_section = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        '[aria-label*="Travellers"]')))
    traveller_section.click()

    def click_plus(label, times):
        plus_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            f"[aria-label = 'Increase the number of {label}']")))
        for _ in range(times):
            plus_button.click()


    click_plus("adults", adults-1)
    
    click_plus("children", children)
    if children > 0:
        child_selects = wait.until(
            lambda driver: driver.find_elements(
                By.CSS_SELECTOR,
                'select[id^="age-traveler_selector_children_age_selector-"]'
        )
    )

        for select_box, age in zip(child_selects, children_ages):
            Select(select_box).select_by_value(str(age))
            
    click_plus("infants on lap", infants_lap)

    if infants_lap > 0:
        time.sleep(1)

        all_selects = driver.find_elements(By.TAG_NAME, "select")

        infant_lap_selects = []

        for select_box in all_selects:
            label = select_box.get_attribute("aria-label") or ""
            element_id = select_box.get_attribute("id") or ""

            if "infant" in label.lower() or "infant" in element_id.lower():
                infant_lap_selects.append(select_box)

        for select_box, age in zip(infant_lap_selects[:infants_lap], infants_lap_ages):
            Select(select_box).select_by_value(str(age))
    
    click_plus("infants in seat", infants_seat)
    if infants_seat > 0:
        infant_seat_selects = wait.until(
            lambda driver: driver.find_elements(
                By.CSS_SELECTOR,
                'select[id^="age-traveler_selector_infants_in_seat_age_selector-"]'
        )
    )

        for select_box, age in zip(infant_seat_selects, infants_seat_ages):
            Select(select_box).select_by_value(str(age))

    class_selection = wait.until(EC.visibility_of_element_located((
        By.CSS_SELECTOR,
        "select[aria-label*='Cabin class']")))
    select = Select(class_selection)
    cabin_values = {
    "Economy": "COACH",
    "Premium economy": "ECONOMY_PREMIUM",
    "Business class": "BUSINESS",
    "First class": "FIRST_CLASS"
    }   

    select.select_by_value(cabin_values[cabin_class])
    try:
        done_travellers = wait.until(
            EC.element_to_be_clickable(
                (
                By.XPATH,
                "//button[contains(., 'Done')]"
            )
        )
    )
        driver.execute_script("arguments[0].click();", done_travellers)
    except:
        pass
    submit = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            "//button[contains(., 'Search')]"
        )
    )
)

    driver.execute_script("arguments[0].click();", submit)
    time.sleep(3)
    try:
        price = driver.find_element(
            By.XPATH,
            "//span[contains(text(),'Current lowest price:')]/following-sibling::span"
        )
        return price.text
    except:
        return None
        





