import time
import random
from typing import Tuple, Any

from bs4 import BeautifulSoup as bsp
from bs4.element import Tag

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

sam_smith = "https://open.spotify.com/artist/2wY79sveU1sp5g7SokKOiI"
birdy = "https://open.spotify.com/artist/2WX2uTcsvV5OnS0inACecP"
URL = sam_smith

# The artist page loads 5 top tracks items only but reveals more on clicking
# the 'SEE MORE' button. (volatile)
BUTTON_XPATH = "//div/text()[contains(., 'See')]/ancestor::button"  # or "//button[descendant::div]"
BUTTON_XPATH_DISCRIPTOR = (By.XPATH, BUTTON_XPATH)


def random_wait_for(start=1, end=3):
    secs = random.randrange(start, end)
    time.sleep(secs)


def check_page_load_finish(locator: Tuple) -> bool:
    time_to_wait = 10
    try:
        res = WebDriverWait(browser, time_to_wait).until(
            EC.presence_of_all_elements_located(locator)
        )
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Locator NOT FOUND: {locator[1]} in time of {time_to_wait} secs")
        return False, None
    finally:
        return True, res


service_obj = ChromeService(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service_obj)
browser.get(URL)
random_wait_for(end=2)


finished_loading, elem = check_page_load_finish(BUTTON_XPATH_DISCRIPTOR)

if finished_loading:
    print("Found!!!!!!!!!!!!!!")
else:
    print("Something wrong")

page_html = None
try:
    if elem is not None:
        # ActionChains(browser).move_to_element(elem[0]).click(elem[0])
        browser.execute_script("arguments[0].click();", elem[0])
except ElementClickInterceptedException as e:
    print("Couldn't click element")
else:
    page_html = browser.page_source

soup = bsp(page_html, "html.parser")


def _get_artist_name(html):
    return str(soup.title.string).split()[-1].strip()


def _get_artist_track_data(html: Tag) -> Tuple:
    track_row = html.find(attrs={"data-testid": "tracklist-row"})

    position = int(track_row.contents[0].span.string)
    track_name = str(track_row.contents[1].div.string)
    playcount = str(track_row.contents[2].div.string)

    return position, track_name, playcount


artist_name = _get_artist_name(soup)

# //*[@aria-rowindex] -> list of the tracks
result = []
for table_item in soup.find_all(attrs={"aria-rowindex": True}):
    data = _get_artist_track_data(table_item)

    # DEBUG ---
    position, track_name, playcount = data
    print(position, artist_name, track_name, playcount)
    # --- DEBUG

    result.append(data)

print(result)
