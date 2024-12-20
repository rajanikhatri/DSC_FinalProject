### Research Question: What is the most popular type of housing and average pricing by zip code in ohio?

# general
import pandas as pd
import numpy as np

# web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# api
import requests as r
import json
import os

# pdf
from PyPDF2 import PdfReader
from img2table.document import Image
from img2table.ocr import TesseractOCR


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
                "Demographic",
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
            "Property_data_type",
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
    output_path = "OH_Demographic_Data.csv"
    structured_data.to_csv(output_path, index=False)

    print(f"Excel data processing completed. CSV file created at: {output_path}")


def csv_housingdata():
    # Define the file path and load the dataset
    file_path = "Data/Housing and rental csv dataset/Metro_mlp_uc_sfrcondo_sm_month.csv"
    data = pd.read_csv(file_path)

    # Step 1: Filter data for Ohio
    oh_data = data[data['StateName'] == 'OH']

    # Create a list of WV regions to remove
    wv_regions = [
        "Huntington, WV",
        "Point Pleasant, WV",
        "Weirton, WV",
        "Wheeling, WV"
    ]

    # Remove the WV regions
    oh_data = oh_data[~oh_data['RegionName'].isin(wv_regions)]
    print(f"Removed {len(wv_regions)} WV regions from the dataset")

    #  Restructure the data from wide to long format
    oh_data_long = oh_data.melt(
        id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName"],
        var_name="Date",
        value_name="HousingPrice"
    )

    #  Process date information
    oh_data_long["Date"] = pd.to_datetime(oh_data_long["Date"], errors="coerce")
    oh_data_long["Year"] = oh_data_long["Date"].dt.year

    #  Handle missing values
    oh_data_long = oh_data_long.sort_values(['RegionName', 'Date'])

    # Forward fill for up to 3 consecutive missing values
    oh_data_long["HousingPrice_FFill"] = oh_data_long.groupby("RegionName")["HousingPrice"].transform(
        lambda x: x.fillna(method='ffill', limit=3)
    )

    #  Region-specific median fill
    oh_data_long["HousingPrice_Filled"] = oh_data_long.groupby(["RegionName", "Year"])["HousingPrice_FFill"].transform(
        lambda x: x.fillna(x.median())
    )

    #  Overall year median fill
    oh_data_long["HousingPrice_Filled"] = oh_data_long.groupby("Year")["HousingPrice_Filled"].transform(
        lambda x: x.fillna(x.median())
    )

    #  Calculate annual statistics
    annual_avg_prices = oh_data_long.groupby(
        ["RegionID", "SizeRank", "RegionName", "RegionType", "StateName", "Year"],
        as_index=False
    ).agg({
        "HousingPrice_Filled": [
            ("AverageHousingPrice", "mean"),
            ("MedianHousingPrice", "median"),
            ("MinPrice", "min"),
            ("MaxPrice", "max")
        ]
    }).round(2)

    # Clean up the column names
    annual_avg_prices.columns = [col[1] if col[1] != '' else col[0] for col in annual_avg_prices.columns]

    # Add Property_data_category column
    annual_avg_prices["Property_data_type"] = "Housing"

    cols = [
        "Year", "Property_data_type", "RegionID", "SizeRank", "RegionName",
        "RegionType", "StateName", "AverageHousingPrice", "MedianHousingPrice",
        "MinPrice", "MaxPrice"
    ]
    annual_avg_prices = annual_avg_prices[cols]

    # Sort the data by Year and then RegionName
    annual_avg_prices = annual_avg_prices.sort_values(by=["Year", "RegionName"], ascending=[True, True])

    # Save the results to a CSV file
    output_path = "OH_Housing_Data.csv"
    annual_avg_prices.to_csv(output_path, index=False)

    # Print confirmation messages
    print(f"Final dataset created and saved at: {output_path}")


def csv_rentaldata():
    # Load the rental CSV file
    file_path = "Data/Housing and rental csv dataset/FMR_All_1983_2025.csv"
    data = pd.read_csv(file_path, encoding='latin-1')

    # Create filter for Ohio data
    Ohio_Filter = (
            data['areaname25'].str.contains(", OH")
    )

    oh_data = data[Ohio_Filter]

    # Check for duplicates in original Ohio data
    duplicates = oh_data[oh_data.duplicated()]
    print("\nChecking for duplicates in original data:")
    print(f"Number of duplicate rows: {len(duplicates)}")
    if len(duplicates) > 0:
        print("Duplicate rows found in:")
        print(duplicates['areaname25'].values)

    # Create empty list to store the data
    all_data = []

    # Process data for each year (2018-2024)
    for year in range(18, 25):
        year_str = f"{year:02d}"
        year_cols = [f'fmr{year_str}_{i}' for i in range(5)]  # 0-4 bedrooms

        # Check for missing values in this year's columns
        missing_values = oh_data[year_cols].isnull().sum()
        if missing_values.sum() > 0:
            print(f"\nMissing values for year 20{year_str}:")
            for col, count in missing_values.items():
                if count > 0:
                    print(f"{col}: {count} missing values")

        # Collect data for each region
        for _, row in oh_data.iterrows():
            all_data.append({
                'Year': 2000 + int(year_str),  # Convert to full year (e.g., 2018, 2019)
                'property_data_type': 'Rental',
                'RegionName': row['areaname25'],
                'StudioMonthlyRent': row[f'fmr{year_str}_0'],
                '1BedMonthlyRent': row[f'fmr{year_str}_1'],
                '2BedMonthlyRent': row[f'fmr{year_str}_2'],
                '3BedMonthlyRent': row[f'fmr{year_str}_3'],
                '4BedMonthlyRent': row[f'fmr{year_str}_4'],
            })

    # Convert to DataFrame and sort
    result_df = pd.DataFrame(all_data)
    result_df = result_df.sort_values(['Year', 'RegionName'])

    # Save to CSV
    output_path = "OH_Rental_Data.csv"
    result_df.to_csv(output_path, index=False)

    print(f"\nData saved to: {output_path}")
    print(f"Total records: {len(result_df)}")


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

    df = pd.DataFrame(columns=['Property Title', 'Property Address', 'Price', 'Bedrooms'])

    # get listings and collect relevant data
    listings = driver.find_elements(By.TAG_NAME, 'article')
    for listing in listings:
        property_title = listing.find_element(By.CLASS_NAME, 'js-placardTitle').text
        property_address = listing.find_element(By.CLASS_NAME, 'property-address').text
        zip_code = property_address.split(' ')[-1]
        price = listing.find_element(By.CLASS_NAME, 'property-pricing').text
        bedrooms = listing.find_element(By.CLASS_NAME, 'property-beds').text
        df.loc[len(df)] = [property_title, property_address, price, bedrooms]

    driver.quit()
    return clean_web_data(df)


def api_data():
    # housing market treds: rentcast.io
    # limited to top 25 by APIs by free trial (25 for testing + 25 for grading = 50 calls)
    ohio_zips = ['45011','43123','44035','44256','43055','43026','44060','43130','43081','45601','43230','44077','45140','43068','43701','45840','43228','43302','43015','45040','45013','45044','43229','44107','45424']
    header = {'accept': 'application/json',
              'X-Api-Key': RENTCAST_API_KEY}
    data = {}
    if os.path.exists('Data/ohio_rentcast_data.json'):
        with open('Data/ohio_rentcast_data.json', 'r') as json_file:
            data = json.load(json_file)
    else:
        # query the api for each zip
        for zip_code in ohio_zips:
            url = f'https://api.rentcast.io/v1/markets?zipCode={zip_code}'
            response = r.get(url, headers=header)
            data[zip_code] = response.json()
        # save data to file to be reused
        with open('Data/ohio_rentcast_data.json', 'w') as json_file:
            json.dump(data, json_file)

    return clean_api_data(data)
    

def pdf_data():
    # housing policy report
    file = 'Data/Official-Final-Report-compressed.pdf'
    reader = PdfReader(file)
    page = reader.pages[12]

    # get table that is saved as an image
    for image in page.images:
        with open('Data/table.jpg', 'wb') as file:
            file.write(image.data)

    # use ocr to read contents
    img = Image(src='Data/table.jpg')
    ocr = TesseractOCR(lang="eng")
    img_table = img.extract_tables(ocr=ocr)[0]
    rows = []
    for id_row, row in enumerate(img_table.content.values()):
        df_row = []
        for id_col, cell in enumerate(row):
            df_row.append(cell.value)
        rows.append(df_row)

    # convert to dataframe
    df = pd.DataFrame(rows[1:], columns=rows[0], index=None)
    return clean_pdf_data(df)


# data cleaning methods
def clean_web_data(data):
    # reformat columns from matching listing to the format for merging
    df = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    # extract zip code from each address
    df['zip_code'] = data['Property Address'].apply(lambda x: x.split(' ')[-1])
    # designate the type as a rental
    df['property_data_type'] = data['Bedrooms'].apply(lambda x: f'{x} rent')
    # calculate average rent value or unknown = NaN
    df['value'] = data['Price'].apply(lambda x: (int(x.split('$')[-1].replace(',', '')) + int(x.split(' ')[0].strip('$').replace(',', ''))) / 2 if '-' in x else int(x.split('$')[-1].replace(',', '')) if '$' in x else np.nan)
    df['value'].fillna(df['value'].median(), inplace=True)
    df['year'], df['month'] = 2024, 12
    return df


def clean_api_data(data):
    # Clean API data by only saving relevant columns and adjusting granularity when converting to df
    df = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    for zip_code, zip_data in data.items():
        sale_data = zip_data.get('saleData')
        if sale_data.get('dataByBedrooms'):
            for property_type in sale_data.get('dataByBedrooms'):
                # Get data from current year by bedroom
                # average
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom average price", property_type.get('averagePrice'), 2024, 12]
                df.loc[len(df)] = row
                # median
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom median price", property_type.get('medianPrice'), 2024, 12]
                df.loc[len(df)] = row
                # min
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom min price", property_type.get('minPrice'), 2024, 12]
                df.loc[len(df)] = row
                # max
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom max price", property_type.get('maxPrice'), 2024, 12]
                df.loc[len(df)] = row
        if sale_data.get('dataByPropertyType'):
            for property_type in sale_data.get('dataByPropertyType'):
                # Get data from current year by property type
                # average
                row = [zip_code, f"{property_type.get('propertyType')} average price", property_type.get('averagePrice'), 2024, 12]
                df.loc[len(df)] = row
                # median
                row = [zip_code, f"{property_type.get('propertyType')} median price", property_type.get('medianPrice'), 2024, 12]
                df.loc[len(df)] = row
                # min
                row = [zip_code, f"{property_type.get('propertyType')} min price", property_type.get('minPrice'), 2024, 12]
                df.loc[len(df)] = row
                # max
                row = [zip_code, f"{property_type.get('propertyType')} max price", property_type.get('maxPrice'), 2024, 12]
                df.loc[len(df)] = row
        # Get historical data
        for date, historical_data in sale_data.get('history').items():
            if historical_data.get('dataByBedrooms'):
                for property_type in historical_data.get('dataByBedrooms'):
                    # average
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom average price", property_type.get('averagePrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # median
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom median price", property_type.get('medianPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # min
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom min price", property_type.get('minPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # max
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom max price", property_type.get('maxPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
            if historical_data.get('dataByPropertyType'):
                for property_type in historical_data.get('dataByPropertyType'):
                    # average
                    row = [zip_code, f"{property_type.get('propertyType')} average price", property_type.get('averagePrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # median
                    row = [zip_code, f"{property_type.get('propertyType')} median price", property_type.get('medianPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # min
                    row = [zip_code, f"{property_type.get('propertyType')} min price", property_type.get('minPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # max
                    row = [zip_code, f"{property_type.get('propertyType')} max price", property_type.get('maxPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
        rent_data = zip_data.get('rentalData')
        if rent_data.get('dataByBedrooms'):
            for property_type in rent_data.get('dataByBedrooms'):
                # Get data from current year by bedroom
                # average
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom average rent", property_type.get('averagePrice'), 2024, 12]
                df.loc[len(df)] = row
                # median
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom median rent", property_type.get('medianPrice'), 2024, 12]
                df.loc[len(df)] = row
                # min
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom min rent", property_type.get('minPrice'), 2024, 12]
                df.loc[len(df)] = row
                # max
                row = [zip_code, f"{property_type.get('bedrooms')} bedroom max rent", property_type.get('maxPrice'), 2024, 12]
                df.loc[len(df)] = row
        if rent_data.get('dataByPropertyType'):
            for property_type in rent_data.get('dataByPropertyType'):
                # Get data from current year by property type
                # average
                row = [zip_code, f"{property_type.get('propertyType')} average rent", property_type.get('averagePrice'), 2024, 12]
                df.loc[len(df)] = row
                # median
                row = [zip_code, f"{property_type.get('propertyType')} median rent", property_type.get('medianPrice'), 2024, 12]
                df.loc[len(df)] = row
                # min
                row = [zip_code, f"{property_type.get('propertyType')} min rent", property_type.get('minPrice'), 2024, 12]
                df.loc[len(df)] = row
                # max
                row = [zip_code, f"{property_type.get('propertyType')} max rent", property_type.get('maxPrice'), 2024, 12]
                df.loc[len(df)] = row
        # Get historical data
        for date, historical_data in rent_data.get('history').items():
            if historical_data.get('dataByBedrooms'):
                for property_type in historical_data.get('dataByBedrooms'):
                    # average
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom average rent", property_type.get('averagePrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # median
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom median rent", property_type.get('medianPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # min
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom min rent", property_type.get('minPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # max
                    row = [zip_code, f"{property_type.get('bedrooms')} bedroom max rent", property_type.get('maxPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
            if historical_data.get('dataByPropertyType'):
                for property_type in historical_data.get('dataByPropertyType'):
                    # average
                    row = [zip_code, f"{property_type.get('propertyType')} average rent", property_type.get('averagePrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # median
                    row = [zip_code, f"{property_type.get('propertyType')} median rent", property_type.get('medianPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # min
                    row = [zip_code, f"{property_type.get('propertyType')} min rent", property_type.get('minPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
                    # max
                    row = [zip_code, f"{property_type.get('propertyType')} max rent", property_type.get('maxPrice'), date[:4], date[5:]]
                    df.loc[len(df)] = row
    # Count and print missing values
    print('Missing values before:')
    print(df.isnull().sum())
    # Drop rows with missing values
    df = df.dropna()
    print('Missing values after dropna:')
    print(df.isnull().sum())
    return df


def clean_pdf_data(data):
    # flatten and drop irrelevant columns & rows
    df = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    df['value'] = data['Median Listing Price']
    # drop last row of percentage data
    df = df.drop(df.tail(1).index)
    # to designate all of ohio
    df['zip_code'] = '4xxxx'
    df['property_data_type'] = data.columns.tolist()[1]
    df['value'] = data['Median Listing Price'].apply(lambda x: x.strip('$').replace(',', '') if isinstance(x, str) else np.nan)
    df['year'] = data['Year']
    df['month'] = '12' # assuming data was collected at the end of the year
    print('Missing values before:')
    print(df.isnull().sum())
    # Drop rows with missing values
    df = df.dropna()
    print('Missing values after dropna:')
    print(df.isnull().sum())
    print(df)


# merge methods
def merge_data(dfs):
    # merge all data sources
    merged = pd.concat(dfs)
    merged['property_data_type'] = merged['property_data_type'].apply(lambda x: str(x).lower())
    merged['value'] = merged['value'].apply(lambda x: round(float(x.replace(',', '')), 2) if isinstance(x, str) else x)
    merged = merged.drop_duplicates()
    return merged


def melt_excel(csv):
    df_ready = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    df = pd.read_csv(csv)
    # flatten data
    flattened_df = pd.melt(df, id_vars=["Property_data_type", "Year", "Population group"], var_name="value name",value_name="value")
    df_ready["property_data_type"] = flattened_df["Population group"].str.cat(flattened_df["value name"], sep=" ")
    df_ready["value"] = flattened_df["value"]
    df_ready["year"] = flattened_df["Year"]
    df_ready["month"] = 12
    df_ready["zip_code"] = '4xxxx'
    return df_ready


def melt_csv(csv1, csv2):
    df_ready = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    df_ready2 = pd.DataFrame(columns=['zip_code','property_data_type','value', 'year', 'month'])
    df1 = pd.read_csv(csv1)
    df2 = pd.read_csv(csv2)
    # flatten housing data
    flattened_df1 = pd.melt(df1, id_vars=["RegionID", "SizeRank", "RegionName", "RegionType", "StateName", "Year", "Property_data_type"], var_name="value name",value_name="value")
    df_ready["value"] = flattened_df1["value"]
    df_ready["property_data_type"] = flattened_df1.apply(
                                        lambda row: row["value name"] + " " + row["Property_data_type"]
                                        if "Housing" not in row["value name"] else row["value name"], axis=1)   
    df_ready["year"] = flattened_df1["Year"]
    df_ready["month"] = 12
    df_ready["zip_code"] = flattened_df1["RegionID"].astype(int)
    # flatten rental data
    flattened_df2 = pd.melt(df2, id_vars=["RegionName", "Year", "property_data_type"], var_name="value name",value_name="value")
    df_ready2["value"] = flattened_df2["value"]
    df_ready2["property_data_type"] = flattened_df2["value name"]
    df_ready2["year"] = flattened_df2["Year"]
    df_ready2["month"] = 12
    # tried to get zip from housing data but the region names are different
    #flattened_df2 = flattened_df2.merge(flattened_df1[["RegionName", "RegionID"]], on="RegionName", how="left")
    df_ready2["zip_code"] = '4xxxx'

    df_ready = pd.concat([df_ready, df_ready2])
    return df_ready


def add_calculations(df):
    df['annual_rent'] = df.apply(lambda row: row['value'] * 12 if 'rent' in str(row['property_data_type']) else 'n/a', axis=1)
    inflation_rate = .028 # average inflation rate in the US over past 5 years
    df['home value increase from inflation'] = df.apply(lambda row: round(row['value'] * inflation_rate, 2) if ('price' in str(row['property_data_type']) and int(row['year']) < 2024) else 'n/a', axis=1)
    return df


if __name__ == "__main__":

    print('Extracting data...')
    
    print("Web scraping....")
    try:
        df_web = web_scraping_data()
        print("Completed web scraping.")
    except Exception as e:
        print(f"Error: {e}")
        print("Web scraping failed.")

    print("Extracting Excel data....")
    try:
        excel_data()
        print("Excel data extraction completed.")
    except Exception as e:
        print(f"Error: {e}")
        print("Error in Excel data extraction.")

    print("Extracting API data....")
    try:
        df_api = api_data()
        print("API data extraction completed.")
    except Exception as e:
        print(f"Error: {e}")
        print("Error in API data extraction.")

    print("Extracting PDF data....")
    try:
        df_pdf = pdf_data()
        print("PDF data extraction completed.")
    except Exception as e:
        print(f"Error: {e}")
        print("Error in PDF data extraction.")

    print("Extracting CSV housing data....")
    try:
        csv_housingdata()
        print("CSV housing data extraction completed.")
    except Exception as e:
        print(f"Error: {e}")
        print("Error in CSV housing data extraction.")

    print("Extracting CSV rental data....")
    try:
        csv_rentaldata()
        print("CSV rental data extraction completed.")
    except Exception as e:
        print(f"Error: {e}")
        print("Error in CSV rental data extraction.")

    print("Merging data....")
    df_excel = melt_excel('OH_Demographic_Data.csv')
    df_csv = melt_csv('OH_Housing_Data.csv', 'OH_Rental_Data.csv')

    df_merged = merge_data([df_web, df_api, df_pdf, df_excel, df_csv])
    df_final = add_calculations(df_merged)
    df_final.to_csv('group_4_final.csv', index=False)
    print("Data merged and saved to group_4_final.csv")