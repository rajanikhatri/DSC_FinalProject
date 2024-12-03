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

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, 'li'))
    )

    listings = driver.find_elements(By.TAG_NAME, 'li')
    for listing in listings:
        print(listing)

    driver.quit()


def api_data():
    # housing market treds: rentcast.io
    pass


def pdf_data():
    # housing policy report (https://www.huduser.gov/portal/chma/oh.html)
    pass


if __name__ == '__main__':
    print("Ohio housing data analysis final project")
    web_scraping_data()