import requests as r
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

RENTCAST_API_KEY = "a0de751d717e405ca5eea0581ea338a4"

# Data extraction methods
def excel_data():
    # demographics excel spreadsheet
    pass


def csv_data():
    # housing and rental costs
    pass


def web_scraping_data():
    # rental listings (Apartments.com)
    url = 'https://www.apartments.com/oh/'

    # create webdriver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, 'li'))
    )

    df = pd.DataFrame(columns=['Property Title', 'Property Address', 'Zip Code', 'Price', 'Bedrooms'])

    # get listings and collect relevant data
    listings = driver.find_elements(By.TAG_NAME, 'article')
    for listing in listings:
        property_title = listing.find_element(By.CLASS_NAME, 'js-placardTitle').text
        property_address = listing.find_element(By.CLASS_NAME, 'property-address').text
        zip_code = property_address.split(' ')[-1]
        price = listing.find_element(By.CLASS_NAME, 'property-pricing').text
        bedrooms = listing.find_element(By.CLASS_NAME, 'property-beds').text
        df.iloc[len(df)] = [property_title, property_address, zip_code, price, bedrooms]

    driver.quit()
    return df


def api_data():
    # housing market treds: rentcast.io
    pass


def pdf_data():
    # housing policy report (https://www.huduser.gov/portal/chma/oh.html)
    pass


# data cleaining methods


def merge_data():
    # merge all data sources
    pass


if __name__ == '__main__':
    print('Web scraping....')
    try:
        web_scraping_data()
        print('Completed web scraping')
    except Exception as e:
        print(f'Error: {e}')
        print('Web scraping failed')