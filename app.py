import json

from flask import Flask, request, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from typing import Optional

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
# A package to have a chromedriver always up-to-date.
from webdriver_manager.chrome import ChromeDriverManager

USERNAME = "webscrapperdcl"
PASSWORD = "Dcl123456"
ENDPOINT = "pr.oxylabs.io:7777"


def chrome_proxy(user: str, password: str, endpoint: str) -> dict:
    wire_options = {
        "proxy": {
            # "http": f"http://{user}:{password}@{endpoint}",
            "https": f"https://{user}:{password}@{endpoint}",
        }
    }

    return wire_options


app = Flask(__name__)


# Initialize the browser when the Flask app starts


@app.route('/check_availability', methods=['POST'])
def availability_checker():
    if request.method == 'POST':
        manage_driver = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        proxies = chrome_proxy(USERNAME, PASSWORD, ENDPOINT)
        print(proxies)
        driver = webdriver.Chrome(
            service=manage_driver, options=options, seleniumwire_options=proxies
        )
        # chrome_options.add_argument('--headless')  # Run Chrome in headless mode
        try:
            # Get the address from the request
            street_address = request.form.get('q4_streetAddress')
            zip_code = request.form.get('q5_zipcode')

            address_data = f'{street_address},{zip_code}'

            # Open the URL
            driver.get("https://www.t-mobile.com/isp/eligibility?icid=HE__19HMEINTPL_D2U90RACRINA9I116498&channel=d2c")

            # Wait for the Dealer Code input field to be visible
            dealer_code_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "mat-input-2")))

            # Manually enter "2323"
            dealer_code_input.send_keys("2323")

            # Wait for the submit button to become clickable
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='btn-cta mat-button mat-button-base']")))

            # Click the submit button
            submit_button.click()

            # Wait for the pop-up to close
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "mat-input-2")))

            # Fill in phone number
            phone_input = driver.find_element(By.ID, "mat-input-0")
            phone_input.send_keys("8888788888")

            # Fill in home address
            address_input = driver.find_element(By.ID, "mat-input-1")
            address_input.send_keys(address_data)

            # Wait for address suggestions to appear
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "mat-option-text")))

            # Choose the first suggested address
            suggested_address = driver.find_element(By.CLASS_NAME, "mat-option-text")
            suggested_address.click()
            time.sleep(5)
            # Wait for the Check Availability button to be clickable
            check_availability_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='form']/form/div/button"))
            )
            check_availability_button.click()

            # Adding a delay of 5 seconds to ensure the page fully loads
            time.sleep(5)

            availability_status = None

            # Get the page source
            page_source = driver.page_source

            # Check for specific texts on the page
            if 'Submit' in page_source and 'Try a different location' in page_source:
                availability_status = "LITE AVAILABLE"
            elif 'Submit' in page_source:
                availability_status = "HINT AVAILABLE"
            elif 'Join waiting list' in page_source:
                availability_status = "NOT AVAILABLE"
            print(availability_status)
            return render_template('index.html', availability_status=availability_status)


        except Exception as e:

            print(str(e))
            return jsonify({"error": str(e)}), 400
        finally:
            # Close the browser after each request
            driver.quit()
    return render_template('index.html', availability_status=None)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
