import csv
import random
import time
from typing import List, Tuple

from bs4 import BeautifulSoup as bsp
from bs4.element import Tag
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# from selenium.webdriver import ActionChains

sam_smith = "https://open.spotify.com/artist/2wY79sveU1sp5g7SokKOiI"
birdy = "https://open.spotify.com/artist/2WX2uTcsvV5OnS0inACecP"
boy = "https://open.spotify.com/artist/1Cd373x8qzC7SNUg5IToqp"
URL = birdy
MAX_WAIT = 10


def random_wait_for(start=1, end=3):
    secs = random.randrange(start, end)
    time.sleep(secs)


def _has_page_finished_loading(locator: Tuple) -> bool:
    time_to_wait = MAX_WAIT
    try:
        WebDriverWait(browser, time_to_wait).until(
            EC.presence_of_all_elements_located(locator)
        )
        return True
    except (TimeoutException, NoSuchElementException) as e:
        print(
            f"Page Finished Loading Test Failed: {locator[1]}, {time_to_wait} secs\n{e}"
        )
        return False


def _click_expanding_button():
    # The artist page loads 5 top tracks items only but reveals more on clicking
    # the 'SEE MORE' button. (volatile)
    BUTTON_XPATH = "//div/text()[contains(., 'See')]/ancestor::button"  # or "//button[descendant::div]"
    start_time = time.time()
    while True:
        elems = browser.find_elements(By.XPATH, BUTTON_XPATH)
        if elems:
            try:
                # ActionChains(browser).move_to_element(elem[0]).click(elem[0])
                browser.execute_script("arguments[0].click();", elems[0])
            except ElementClickInterceptedException as e:
                print("Couldn't click element")
                raise e
            else:
                print("Expanding button found and clicked")
                return True
        else:
            if time.time() - start_time > MAX_WAIT:
                return False
            random_wait_for(end=2)


def _check_for_popular_list(html):
    rows = soup.find_all(attrs={"aria-rowindex": True})
    if not len(rows):
        raise NoSuchElementException("NO track list found")


def _get_page_doc():
    html = None
    if finished:
        html = bsp(browser.page_source, "html.parser")
    return html


def _browser_setup():
    service_obj = ChromeService(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service_obj)
    browser.get(URL)
    random_wait_for(end=2)
    return browser


def _browser_teardown():
    pass


browser = _browser_setup()

finished = _has_page_finished_loading(
    (By.XPATH, "//h2[text()[contains(., 'Popular')]]")
)

clicked = _click_expanding_button()

soup = _get_page_doc()

if not clicked:
    _check_for_popular_list(soup)


def _get_artist_name(html: Tag):
    return str(html.title.string).split("–")[-1].strip()


def _get_artist_track_data(html: Tag) -> Tuple:
    track_row = html.find(attrs={"data-testid": "tracklist-row"})

    position = int(track_row.contents[0].span.string)
    track_name = str(track_row.contents[1].div.contents[0].string)
    playcount = str(track_row.contents[2].div.string)

    return position, track_name, playcount


artist_name = _get_artist_name(soup)


def _parse_doc(html: Tag) -> List:
    # //*[@aria-rowindex] -> list of the tracks
    result = []
    for table_item in html.find_all(attrs={"aria-rowindex": True}):
        data = _get_artist_track_data(table_item)

        # DEBUG ---
        position, track_name, playcount = data
        print(position, artist_name, track_name, playcount)
        # --- DEBUG

        result.append(data)
    return result


def _save_to_csv(data):
    with open("artisttrack.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["position", "artist name", "track title", "playcount"])
        for item in data:
            L = list(item)
            L.insert(1, artist_name)
            writer.writerow(L)


_save_to_csv(data=_parse_doc(soup))
