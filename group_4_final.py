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
    # neighborhood demographic data
    # Paths to the Excel files and corresponding years
    file_paths = [
        ("Data/Demographic Excel Dataset/ACSST5Y2020.S0501-2024-12-05T161503.xlsx", 2023),
        ("Data/Demographic Excel Dataset/ACSST1Y2023.S0501-2024-12-05T050120.xlsx", 2022),
        ("Data/Demographic Excel Dataset/ACSST1Y2022.S0501-2024-12-05T050308.xlsx", 2021),
        ("Data/Demographic Excel Dataset/ACSST1Y2021.S0501-2024-12-05T161344.xlsx", 2020),
        ("Data/Demographic Excel Dataset/ACSST1Y2019.S0501-2024-12-05T161533.xlsx", 2019),
        ("Data/Demographic Excel Dataset/ACSST1Y2018.S0501-2024-12-05T161558.xlsx", 2018)
    ]

# Function to clean numbers (e.g., remove commas)
#I keep this if I need to work on percentage too,
#def clean_number(value):
    #try:
       # return float(str(value).replace(',', '').strip())
    #except ValueError:
       # return value  # Keep as-is if not a valid number

    # Function to process an Excel file
    def process_file(file_path, year):
        # Load the Excel file
        excel_data = pd.ExcelFile(file_path)
        data = excel_data.parse('Data')

        # Extract data for the given year
        population_groups = data.iloc[0, 1:6].values
        total_population = data.iloc[2, 1:6].values
        employment_status = data.iloc[57, 1:6].values
        civilian_employed = data.iloc[65, 1:6].values
        earnings_for_yearly_workers = data.iloc[92, 1:6].values
        median_earnings_for_male = data.iloc[101, 1:6].values
        median_earnings_for_female = data.iloc[102, 1:6].values
        median_household_income = data.iloc[116, 1:6].values
        average_no_of_workers = data.iloc[117, 1:6].values
        occupied_housing_units = data.iloc[133, 1:6].values
        owner_occupied_housing_units = data.iloc[153, 1:6].values
        avg_household_size_owner = data.iloc[137, 1:6].values
        renter_occupied_housing_units = data.iloc[157, 1:6].values
        avg_household_size_renter = data.iloc[138, 1:6].values

        # Combine data for the year
        rows = []
        for population_index, population_group in enumerate(population_groups):
            rows.append([
                year,
                population_group,
                total_population[population_index],
                employment_status[population_index],
                civilian_employed[population_index],
                earnings_for_yearly_workers[population_index],
                median_earnings_for_male[population_index],
                median_earnings_for_female[population_index],
                median_household_income[population_index],
                average_no_of_workers[population_index],
                occupied_housing_units[population_index],
                owner_occupied_housing_units[population_index],
                avg_household_size_owner[population_index],
                renter_occupied_housing_units[population_index],
                avg_household_size_renter[population_index]
            ])
        return rows

    # Process all files and combine the data
    all_rows = []
    for file_path, year in file_paths:
        all_rows.extend(process_file(file_path, year))

    # Create the DataFrame
    structured_data = pd.DataFrame(
        all_rows,
        columns=[
            "Year",
            "Population group",
            "Total Population",
            "Employment Status for 16 years and over",
            "Civilian employed population 16 years and over",
            "Earnings (Full-Time Workers)",
            "Median Earnings for Male",
            "Median Earnings for Female",
            "Median Household Income",
            "Average workers per household",
            "Occupied Housing Units",
            "Owner occupied Housing Units",
            "Average Housing Size by owner-occupied Units",
            "Renter occupied Housing Units",
            "Average Housing Size by renter-occupied Units"
        ]
    )

    # Save to CSV
    output_path = "Ohio_Housing_Status_Population_Income_and_Employment.csv"
    structured_data.to_csv(output_path, index=False)

    print(f"Excel data processing completed. CSV file created at: {output_path}")


def csv_data():
    # housing and rental costs
    pass


def web_scraping_data():
    # rental listings (Apartments.com)
    url = 'https://www.apartments.com/oh/'

    # create webdriver d
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
    ohio_zips = [43085]
    # housing market treds: rentcast.io
    header = {'accept': 'application/json',
              'X-Api-Key': RENTCAST_API_KEY}
    # limited to top 50 by API free trial
    for zip_code in ohio_zips:
        url = f'https://api.rentcast.io/v1/markets?zipCode={zip_code}&dataType=All&historyRange=0'
        response = r.get(url, headers=header)
        data = response.json()
        print(data)
        # process data
        pass


def pdf_data():
    # housing policy report (https://www.huduser.gov/portal/chma/oh.html)
    pass


# data cleaining methods


def merge_data():
    # merge all data sources
    pass


if __name__ == '__main__':
    # print('Web scraping....')
    # try:
    #     web_scraping_data()
    #     print('Completed web scraping')
    # except Exception as e:
    #     print(f'Error: {e}')
    #     print('Web scraping failed')
      
    # print('Extracting Excel data....')
    # try:
    #     excel_data()
    #     print('Excel data extraction completed.')
    # except Exception as e:
    #     print(f'Error in Excel data extraction: {e}')

    print('Extracting API data....')
    try:
        api_data()
        print('API data extraction completed.')
    except Exception as e:
        print(f'Error in API data extraction: {e}')