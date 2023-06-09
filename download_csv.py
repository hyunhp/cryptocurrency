'''
PURPOSE : Donwload csv file from coingecko
'''

# IMPORT LIBRARY
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.service import Service
from selenium import webdriver

import time
from tqdm import tqdm
import os
import pandas as pd
import shutil

from batch_target import extract_batch_coin

import datetime
chrome_path = r'.\\99. setting\\chromedriver'

def download_makedirs(day_of_week, delete : False):
    # GLOBAL VARIABLE
    download_path   = os.getcwd() + '\\historical data\\' + str(day_of_week)
    failed_path     = os.path.join(download_path, 'failed')

    if delete :
        # Delete and recreate the download path if it already exists
        if os.path.exists(download_path):
            shutil.rmtree(download_path)
        os.makedirs(download_path)
    else :
        # Set the download path
        if not os.path.exists(download_path):
            os.makedirs(download_path)

    # Set the failed path 
    if not os.path.exists(download_path + '\\failed'):
        os.makedirs(download_path + '\\failed')
        
    return download_path

# download function
def download_coin_csv(download_path, batch_coin, current_date):
    formatted_date = current_date.strftime('%Y_%m_%d')

    # Set the download preferences
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    # Configure the Selenium webdriver
    options = webdriver.ChromeOptions()
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option("prefs", prefs)

    service = Service(chrome_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.coingecko.com/")
    time.sleep(5)

    failed_name = []
    failed_url = []

    for index, name in tqdm(batch_coin.iterrows(), total=batch_coin.shape[0]):
        url = name['download_csv_url'] + "/historical_data"
        driver.get(url)
        time.sleep(1)

        try:
            # Perform a scroll action to reach the bottom of the page
            body = driver.find_element(By.XPATH, "//body")
            body.send_keys(Keys.END)
            time.sleep(0.5)

            # Wait for the element to be clickable
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/main/div[3]/div/div[1]/div[1]/div[2]")))

            # Click the element
            element.click()
            time.sleep(1)

            # download 
            download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/main/div[3]/div/div[1]/div[1]/div[2]/div/div[2]/div/div/span[2]")))
            download_button.click()
            time.sleep(0.5)

        except:
            failed_name.append(name['coin_name'])
            failed_url.append(url)
            pass
    
    print(f'{current_date} Batch done...')
    
    driver.quit()
    if not len(failed_name) == 0 :
        failed_csv = pd.DataFrame({'name' : failed_name, 
                                   'url' : failed_url})
        failed_csv.to_csv(f'{download_path}\\failed\\{formatted_date}_failed.csv')
        print(f'{len(failed_csv)} / {len(batch_coin)} Failed...')
        

if __name__ == '__main__':
    batch_coin, day_of_week, current_date = extract_batch_coin()
    download_path = download_makedirs(day_of_week, delete=True)
    download_coin_csv(download_path, batch_coin, current_date)