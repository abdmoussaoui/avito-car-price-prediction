import os
import csv
import json
import time
import random
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fake_useragent import UserAgent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename = "../../logs/scraper.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(message)s",
    level = logging.INFO
)
logger = logging.getLogger(__name__)

class AvitoCarScraper:
    """
    A class to scrape car listings from Avito.

    This scraper targets a specific page of car listings on Avito, extracts URLs for individual cars,
    fetches detailed information from each car's page, and saves the data in CSV format.

    Attributes:
        _request_semaphore (asyncio.Semaphore): Limits concurrent HTTP requests to prevent overload.
        _csv_output_dir (str)                 : Directory path for storing CSV output file.
        _field_mappings (dict)                : Maps HTML field names to standardized output keys.
        _base_url (str)                       : The base URL of the Avito page to scrape.
        _page_number (int)                    : The page number of car listings to scrape.
        _used_proxies (list)                  : Tracks proxies that have been used to avoid repetition.
        _proxies (list)                       : List of available proxies loaded from a file.
        _css_selectors (dict)                 : CSS selectors for scraping data, loaded from a file.
    """
    _request_semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests
    _csv_output_dir = "../../data/raw"
    _field_mappings = {
        "Titre"             : "car_title",
        "Prix"              : "car_price",
        "Localisation"      : "car_location",
        "Date_publication"  : "car_post_time",
    }
    CSV_FIELDNAMES = [
        "Titre", "Prix", "Localisation", "Date_publication", "Année-Modèle",
        "Boite de vitesses", "Type de carburant", "Kilométrage", "Marque",
        "Modèle", "Nombre de portes", "Origine", "Première main",
        "Puissance fiscale", "État", "Équipements"
    ]

    def __init__(self, base_url: str, page_number: int):
        """
        Initialize the AvitoCarScraper with a URL and page number.

        Args:
            :param base_url (str)   : The base URL of the Avito page with car listings.
            :param page_number (int): The page number to scrape
        """
        self._base_url      = base_url
        self._page_number   = page_number
        self._used_proxies  = []
        self._proxies       = self._load_proxies()
        self._css_selectors = self._load_selectors()

    @staticmethod
    def _read_json_file(file_name: str) -> list | dict:
        """
        Read and parse a JSON file from the storage directory.

            :param file_name (str): Name of the JSON file to read.
            :return list | dict   : Parsed JSON data, or an empty list if the file is invalid/missing.
        """
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as err:
            logger.error(f"Failed to read {file_name}: {err}")
            return []

    @staticmethod
    async def _fetch_page(session: aiohttp.ClientSession, url: str, params: dict = None,
                          headers: dict = None, proxy: str = None) -> BeautifulSoup | None:
        """
        Asynchronously fetch a webpage and return its parsed content.

        Args:
            :param session (aiohttp.ClientSession): The HTTP session for making requests.
            :param url (str)                      : The URL to fetch.
            :param params (dict, optional)        : Query parameters for the request.
            :param headers (dict, optional)       : Custom HTTP headers.
            :param proxy (str, optional)          : Proxy server address.

        Returns:
            :return BeautifulSoup | None: Parsed HTML content, or None if the request fails.
        """
        headers = headers or {}
        headers.setdefault("User-Agent", UserAgent().random)
        if proxy:
            headers["proxy"] = proxy
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return BeautifulSoup(await response.text(), "lxml")
                logger.error(f"Request failed with status {response.status} for {url}")
                return None
        except Exception as err:
            logger.error(f"Error fetching {url} : {err}")
            return None

    def _load_proxies(self) -> list[str]:
        """Load proxy addresses from 'proxies.json'."""
        proxies_data = self._read_json_file("./config/proxies.json")
        return [proxy["address"] for proxy in proxies_data]

    def _get_random_proxy(self) -> str:
        """
        Select a random unused proxy, resetting the used list if all proxies have been used.

        Returns:
            :return str: A proxy address.
        """
        if len(self._used_proxies) == len(self._proxies):
            self._used_proxies.clear()
        available_proxies = [p for p in self._proxies if p not in self._used_proxies]
        selected_proxy = random.choice(available_proxies)
        self._used_proxies.append(selected_proxy)
        return selected_proxy

    def _load_selectors(self) -> dict:
        """Load CSS selectors from 'selectors.json' for scraping."""
        return self._read_json_file("./config/selectors.json")

    async def scrape_page(self):
        """
        Scrape all car listings from the specified page and save the results.

        This method fetches car URLs from the page, retrieves details for each car concurrently,
        and saves the data to JSON and CSV files.
        """
        async with aiohttp.ClientSession() as session:
            car_urls = await self._extract_car_urls(session)
            start_time = time.time()
            tasks = [self._fetch_car_details(session, url) for url in car_urls]
            car_details_list = await asyncio.gather(*tasks)
            execution_time = time.time() - start_time
            logger.info(f"Scraped page {self._page_number} in {execution_time:.2f} seconds")
            await self._save_to_csv("cars_data.csv", car_details_list)

    async def _extract_car_urls(self, session: aiohttp.ClientSession) -> list[str]:
        """
        Extract URLs for individual car listings from the current page.

        Args:
            :param session (aiohttp.ClientSession): The HTTP session for requests.

        Returns:
            :return list[str]: List of car listing URLs.

        Raises:
            :exception Exception: If car URLs cannot be fetched.
        """
        params = {"o": self._page_number}
        proxy = self._get_random_proxy()
        soup = await self._fetch_page(session, self._base_url, params=params, proxy=proxy)

        if not soup:
            logger.warning(f"Failed to fetch page {self._page_number}")
            raise Exception("Failed to fetch car URLs")

        car_links = soup.select(self._css_selectors["car_url"])
        urls = [link.get("href") for link in car_links]
        logger.info(f"Extracted {len(urls)} car URLs from page {self._page_number}")
        return urls

    async def _fetch_car_details(self, session: aiohttp.ClientSession, url: str) -> dict | None:
        """
        Fetch detailed information for a single car listing.

        Args:
            :param session (aiohttp.ClientSession): The HTTP session for requests.
            :param url (str)                      : The URL of the car's detail page.

        Returns:
            :return dict | None: Car details as a dictionary, or None if fetching fails.
        """
        async with self._request_semaphore:
            soup = await self._fetch_page(session, url, proxy=self._get_random_proxy())
            if not soup:
                return None

            car_info_section = soup.select_one(self._css_selectors["car_general_info"])
            if not car_info_section:
                logger.warning(
                    f"No car info section found at {url} with selector {self._css_selectors['car_general_info']}")
                return None
            car_details = {}
            # Extract general info
            for html_key, output_key in self._field_mappings.items():
                self._extract_general_info(car_info_section, car_details, html_key, output_key)

            # Extract specifications and equipment
            self._extract_specifications(car_info_section, car_details)
            self._extract_equipments(car_info_section, car_details)
            return car_details

    def _extract_general_info(self, soup: BeautifulSoup, car_details: dict, html_key: str, output_key: str):
        """
        Extract a general information field from the car listing page.

        Args:
            :param soup (BeautifulSoup) : Parsed HTML section containing car info.
            :param car_details (dict)   : Dictionary to store extracted data.
            :param html_key (str)       : Key from field_mappings for the HTML field.
            :param output_key (str)     : Key to use in the output dictionary.
        """
        try:
            selector = self._css_selectors.get(output_key)
            if not selector:
                logger.warning(f"No selector found for {output_key}")
                return

            element = soup.select_one(selector)
            if element:
                value = element.get("datetime") if html_key == "Date_publication" else element.text.strip()
                car_details[html_key] = value
            else:
                car_details[html_key] = None
        except Exception as err:
            logger.error(f"Error extracting {output_key}: {err}")

    def _extract_specifications(self, soup: BeautifulSoup, car_details: dict):
        """Extract car specifications from the detail page."""
        try:
            spec_selector = self._css_selectors.get("car_specifications")
            if not spec_selector:
                logger.warning("Missing car specifications selector")
                return

            specs = soup.select(spec_selector)
            for spec in specs:
                key_value = spec.select(self._css_selectors["car_specification"])
                if len(key_value) == 2:
                    car_details[key_value[1].text.strip()] = key_value[0].text.strip()
        except Exception as err:
            logger.error(f"Error extracting specifications: {err}")

    def _extract_equipments(self, soup: BeautifulSoup, car_details: dict):
        """Extract car equipment features from the detail page."""
        try:
            equip_selector = self._css_selectors.get("car_equipments")
            if equip_selector:
                equipments = [equip.text.strip() for equip in soup.select(equip_selector)]
                if equipments:
                    car_details["Équipements"] = equipments
                else:
                    car_details["Équipements"] = []
            else:
                car_details["Équipements"] = []
        except Exception as err:
            logger.error(f"Error extracting equipments: {err}")

    async def _save_to_csv(self, file_name: str, data: list):
        """Asynchronously save car details to a CSV file."""
        await asyncio.to_thread(self._save_to_csv_sync, file_name, data)

    def _save_to_csv_sync(self, file_name: str, data: list):
        """Synchronous helper to save car details to a CSV file."""
        if not data:
            logger.warning("No data to save to CSV")
            return
        file_path = os.path.join(self._csv_output_dir, file_name)
        file_exists = os.path.exists(file_path)
        filtered_data = [item for item in data if item is not None]
        try:
            for car in filtered_data:
                car["Équipements"] = ", ".join(car.get("Équipements", []))
                for field in self.CSV_FIELDNAMES:
                    car.setdefault(field, "null")
            with open(file_path, "a" if file_exists else "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=self.CSV_FIELDNAMES)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(filtered_data)
            logger.info(f"Saved {len(filtered_data)} cars to {file_name}")
        except Exception as err:
            logger.error(f"Error saving to CSV {file_name}: {err}")

async def scrape_multiple_pages(max_pages: int):
    """
    Scrape car listings across multiple pages.

    Args:
        max_pages (int): The maximum number of pages to scrape (exclusive).
    """
    for page in range(1, max_pages):
        scraper = AvitoCarScraper(os.getenv("AVITO_MAIN_URL"), page)
        await scraper.scrape_page()

if __name__ == "__main__":
    logger.info("Starting Avito.ma scrape...")
    start_time = time.time()
    asyncio.run(scrape_multiple_pages(int(os.getenv("SCRAPER_MAX_PAGES"))))
    total_time = time.time() - start_time
    logger.info(f"Scraping completed in {total_time:.2f} seconds ✅")