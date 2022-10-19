import argparse
import csv
import random
import time
import os
from typing import List, Tuple
from datetime import datetime

from bs4 import BeautifulSoup as bsp
from bs4.element import Tag
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from latest_user_agents import get_random_user_agent

# from selenium.webdriver import ActionChains

sam_smith = "https://open.spotify.com/artist/2wY79sveU1sp5g7SokKOiI"
birdy = "https://open.spotify.com/artist/2WX2uTcsvV5OnS0inACecP"
boy = "https://open.spotify.com/artist/1Cd373x8qzC7SNUg5IToqp"
soumond = "https://open.spotify.com/artist/7E3alOtvuTlLjGwjiZ88g6"

URL = sam_smith, birdy, boy, soumond
MAX_WAIT = 10
TODAY = datetime.today().strftime("%Y-%m-%d")


class ArtistPlayCount:
    def __init__(self, cmdargs):
        self.cmdargs = cmdargs
        self.urls = self.cmdargs.URLs

        self.filename = self._get_filename()
        self.button = None

    def fetch(self):
        self.first = True
        for url in self.urls:
            self._browser_setup(url)
            self.finished = self._has_page_finished_loading(
                (By.XPATH, "//h2[text()[contains(., 'Popular')]]")
            )
            self._click_expanding_button()
            # self._get_page_doc()
            self._check_for_popular_list()
            self._save_to_csv(data=self._parse_doc())
            self._browser_teardown()
            self.first = False

    @staticmethod
    def random_wait_for(start=1, end=3):
        secs = random.randrange(start, end)
        time.sleep(secs)

    def _get_filename(self):
        if len(self.urls) > 1:
            return f"{len(self.urls)}_artists_{TODAY}.csv"
        return None

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
                #  and self.clicked is False
                if time.time() - start_time > (MAX_WAIT / 2):
                    break
                self.random_wait_for(end=2)

    def _get_expanding_button(self):
        # The artist page loads 5 top tracks items only but reveals more on clicking
        # the 'SEE MORE' button. (volatile)
        BUTTON_XPATH = "//div/text()[contains(., 'See')]/ancestor::button"  # or "//button[descendant::div]"
        buttons = self.browser.find_elements(By.XPATH, BUTTON_XPATH)
        if buttons:
            self.button = buttons[0]
        else:
            self.button = None

    def _check_for_popular_list(self):
        start = time.time()
        while True:
            self._get_page_doc()
            rows = self.soup.find_all(attrs={"aria-rowindex": True})
            if not len(rows):
                raise NoSuchElementException(
                    f"No Popular tracks list found for this {self.artist_name}"
                )
            elif time.time() - start > MAX_WAIT and len(rows) <= 5:
                if self.cmdargs.verbose:
                    print("Items row couldn't be expanded")
                break
            elif len(rows) > 5:
                break
            self.random_wait_for(end=2)

    def _get_page_doc(self):
        self.soup = None
        if self.finished:
            self.soup = bsp(self.browser.page_source, "html.parser")

    def _browser_setup(self, url):
        user_agent = get_random_user_agent()

        chrome_opt = ChromeOptions()
        if not self.cmdargs.verbose:
            print(user_agent)
            chrome_opt.headless = True
        chrome_opt.add_argument("--no-sandbox")
        chrome_opt.add_argument("--window-size=1420,1080")
        chrome_opt.add_argument("--disable-gpu")
        chrome_opt.add_argument("--log-level=3")
        chrome_opt.add_argument(f"user-agent={user_agent}")

        service_obj = ChromeService(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service_obj, options=chrome_opt)
        self.browser.get(url)

        self.random_wait_for(end=2)

    def _browser_teardown(self):
        self.random_wait_for()
        self.browser.quit()

    def _get_artist_name(self):
        return str(self.soup.title.string).split("–")[-1].strip()

    def _get_artist_track_data(self, html: Tag) -> Tuple:
        track_row = html.find(attrs={"data-testid": "tracklist-row"})

        track_name = str(track_row.contents[1].div.contents[0].string)
        playcount = str(track_row.contents[2].div.string).replace(",", "")

        return track_name, playcount

    def _parse_doc(self) -> List:
        self.artist_name = self._get_artist_name()

        # //*[@aria-rowindex] -> list of the tracks
        result = []
        for table_item in self.soup.find_all(attrs={"aria-rowindex": True}):
            data = self._get_artist_track_data(table_item)
            if self.cmdargs.verbose:
                track_name, playcount = data
                print(self.artist_name, track_name, playcount)
            result.append(data)
        return result

    def _save_to_csv(self, data):
        print(self.first)
        filename = self.filename if self.filename else f"{self.artist_name}.csv"
        mode = "w" if self.first else "a"
        with open(filename, mode, newline="") as csvfile:
            writer = csv.writer(csvfile)
            if self.first:
                writer.writerow(["artist name", "track title", "playcount"])
            for item in data:
                L = list(item)
                L.insert(0, self.artist_name)
                writer.writerow(L)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="artist10",
        # usage="%(prog)s [options] <artist url> [options]",
        description="Fetches artist popular Spotify tracks",
        epilog="Enjoy the program! :)",
        allow_abbrev=False,
        fromfile_prefix_chars="@",
    )

    parser.add_argument(
        "URLs",
        metavar="url(s)",
        type=str,
        nargs="*",
        help=f"the artist url e.g., {boy}",
        default=[random.choice(URL)],
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
        default=os.getcwd(),
        help="Output folder to save results (default is current working directory)",
    )
    args = parser.parse_args()

    if args.verbose:
        print(args.outputdir)
        print(args.URLs)
    # ArtistPlayCount(cmdargs=args).fetch()
