import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from wiki_image_scraping_script import chrome_driver


# Function to extract and return data from the current page
# 페이지에서 데이터 추출
def extract_data(driver):
    data = {}
    try:
        # 제목(명소의 이름) 추출
        title = driver.find_element(By.XPATH,
                                    '//*[@id="thema_wrapper"]/div[2]/div/div/div[3]/div[1]/section/article/h1').text.strip()
        data['명소 이름'] = title

        rows = driver.find_elements(By.XPATH, '//table/tbody/tr')
        for row in rows:
            key = row.find_element(By.XPATH, './/th').text.strip()
            value = row.find_element(By.XPATH, './/td').text.strip()
            data[key] = value
    except NoSuchElementException:
        pass
    return data


# Main scraping logic
def main():
    all_data = []
    for i in range(1, 187):  # Assuming there are 187 pages
        url = f"https://clubrichtour.co.kr/bbs/board.php?bo_table=hPlaceDB&sst=wr_hit&sod=asc&sop=and&page={i}"
        driver = chrome_driver()
        driver.get(url)
        links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@id="fboardlist"]/table/tbody/tr/td[2]/a')))

        for link in links:
            # Open the link in a new tab
            href = link.get_attribute('href')
            driver.execute_script(f"window.open('{href}', '_blank');")
            driver.switch_to.window(driver.window_handles[1])

            # Extract data from the page
            data = extract_data(driver)
            all_data.append(data)

            # Close the current tab and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # Close the driver after each page to avoid resource leakage
        driver.quit()

    # Before writing to the CSV, collect all unique keys from all dictionaries
    all_keys = set()
    for data in all_data:
        all_keys.update(data.keys())

    # Ensure the keys are sorted or in a specific order if required
    keys = sorted(all_keys)

    # Now write to the CSV using these collected keys
    with open('data.csv', 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_data)


if __name__ == "__main__":
    main()
