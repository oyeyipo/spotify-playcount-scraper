import argparse
import csv
import os
import random
import sys
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

URL = sam_smith, birdy, boy
MAX_WAIT = 10


class ArtistPlayCount:
    def __init__(self, url=random.choice(URL)):
        self.url = url

    def fetch(self):
        self._browser_setup()
        self.finished = self._has_page_finished_loading(
            (By.XPATH, "//h2[text()[contains(., 'Popular')]]")
        )
        self._click_expanding_button()
        # self._get_page_doc()
        self._check_for_popular_list()
        self._save_to_csv(data=self._parse_doc())
        self._browser_teardown()

    @staticmethod
    def random_wait_for(start=1, end=3):
        secs = random.randrange(start, end)
        time.sleep(secs)

    def _has_page_finished_loading(self, locator: Tuple) -> bool:
        time_to_wait = MAX_WAIT
        try:
            WebDriverWait(self.browser, time_to_wait).until(
                EC.presence_of_all_elements_located(locator)
            )
            return True
        except (TimeoutException, NoSuchElementException) as e:
            print(
                f"Page Finished Loading Test Failed: {locator[1]}, {time_to_wait} secs\n{e}"
            )
            return False

    def _click_expanding_button(self):
        self.clicked = False
        start_time = time.time()
        while True:
            self._get_expanding_button()
            if self.button:
                try:
                    # ActionChains(browser).move_to_element(elem).click(elem)
                    self.browser.execute_script("arguments[0].click();", self.button)
                except ElementClickInterceptedException as e:
                    print("Couldn't click element")
                    raise e
                else:
                    print("Expanding button found and clicked")
                    self.clicked = True
                    break
            else:
                if time.time() - start_time > MAX_WAIT and self.clicked is False:
                    break
                self.random_wait_for(end=2)

    def _get_expanding_button(self):
        # The artist page loads 5 top tracks items only but reveals more on clicking
        # the 'SEE MORE' button. (volatile)
        BUTTON_XPATH = "//div/text()[contains(., 'See')]/ancestor::button"  # or "//button[descendant::div]"
        self.button = self.browser.find_elements(By.XPATH, BUTTON_XPATH)[0]

    def _check_for_popular_list(self):
        start = time.time()
        while True:
            self._get_page_doc()
            rows = self.soup.find_all(attrs={"aria-rowindex": True})
            if not self.clicked:
                if not len(rows):
                    raise NoSuchElementException("NO tracks list found")
            elif time.time() - start > MAX_WAIT and len(rows) <= 5:
                print("Items row couldn't be expanded")
                break
            elif len(rows) > 5:
                break
            time.sleep(0.5)

    def _get_page_doc(self):
        self.soup = None
        if self.finished:
            self.soup = bsp(self.browser.page_source, "html.parser")

    def _browser_setup(self):
        service_obj = ChromeService(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service_obj)
        self.browser.get(self.url)
        self.random_wait_for(end=2)

    def _browser_teardown(self):
        self.browser.quit()

    def _get_artist_name(self):
        return str(self.soup.title.string).split("–")[-1].strip()

    def _get_artist_track_data(self, html: Tag) -> Tuple:
        track_row = html.find(attrs={"data-testid": "tracklist-row"})

        position = int(track_row.contents[0].span.string)
        track_name = str(track_row.contents[1].div.contents[0].string)
        playcount = str(track_row.contents[2].div.string)

        return position, track_name, playcount

    def _parse_doc(self) -> List:
        self.artist_name = self._get_artist_name()

        # //*[@aria-rowindex] -> list of the tracks
        result = []
        for table_item in self.soup.find_all(attrs={"aria-rowindex": True}):
            data = self._get_artist_track_data(table_item)

            # DEBUG ---
            position, track_name, playcount = data
            print(position, self.artist_name, track_name, playcount)
            # --- DEBUG

            result.append(data)
        return result

    def _save_to_csv(self, data):
        with open(f"{self.artist_name}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["position", "artist name", "track title", "playcount"])
            for item in data:
                L = list(item)
                L.insert(1, self.artist_name)
                writer.writerow(L)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="artist10",
        usage="%(prog)s [options] <artist url> [options]",
        description="Fetches artist popular Spotify tracks",
        epilog="Enjoy the program! :)",
        allow_abbrev=False,
    )
    parser.add_argument(
        "URL", metavar="url", type=str, help=f"the artist url e.g., {boy}"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show browser and print logs",
    )
    parser.add_argument(
        "-o",
        "--outputdir",
        action="store_true",
        help="Output directory to save the file to",
    )

    args = parser.parse_args()

    u, v = args.URL, args.verbose

    print(u, type(u))
    print(v, type(v))
    ArtistPlayCount(url=args.URL).fetch()