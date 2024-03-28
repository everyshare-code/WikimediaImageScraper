from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time,os
import requests
import base64
import cv2
# import logging
import re
import pandas as pd
import numpy as np
# logging.basicConfig(filename='chrome_driver_errors.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger = logging.getLogger(__name__)
def chrome_driver():

    # driver_path = f'{os.path.join(os.path.dirname(__file__), "chromedriver.exe")}'
    # service = Service(executable_path=driver_path)
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument('headless')
    # options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')  # 추가
    options.add_argument('--disable-dev-shm-usage')  # 추가
    options.add_argument('window-size=1920x1080')
    # options.add_argument('--remote-debugging-pipe')
    # options.add_argument('--disable-software-rasterizer')
    # 윈도우
    # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
    # 맥북
    # User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
    # options.add_argument(
    #     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=service, options=options)



def search_images(driver, query):
    """
    Google 이미지 검색 실행
    """
    # driver.get("https://www.google.com/imghp?hl=ko")
    # (WebDriverWait(driver, 4)
    #  .until(EC.visibility_of_element_located((By.XPATH, '//*[@id="APjFqb"]'))))
    # search_box = driver.find_element(By.XPATH,'//*[@id="APjFqb"]')
    # search_box.send_keys(query)
    # search_box.send_keys(Keys.ENTER)
    '''
    wikimedia commons 이미지 검색
    '''
    url=f'https://commons.wikimedia.org/w/index.php?search={query}&title=Special:MediaSearch&go=Go&type=image'
    driver.get(url)



def scroll_page(driver, scrolls=4, delay=3):
    """
    페이지를 스크롤 다운하여 더 많은 이미지 로드. 지정된 횟수만큼 스크롤하고,
    '결과 더보기' 버튼이 보이면 클릭합니다.
    """
    for _ in range(scrolls):
        # 페이지 맨 아래로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)  # 스크롤 이후에 페이지가 로드될 시간을 기다림

        # '결과 더보기' 버튼을 찾고 클릭할 수 있으면 클릭
        '''
        #cdx-image-0 > div:nth-child(2) > div > div > button
        '''
        try:
            more_button = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[value='Load more']"))
            )
            if more_button:
                driver.find_element(By.CSS_SELECTOR,"button[value='Load more']").click()
                time.sleep(delay)  # 더 많은 결과를 로드할 시간 기다림
        except Exception as e:
            print(f"Scrolling completed or '결과 더보기' button not found: {e}")


def collect_image_urls(driver, num_images):
    """
    수집된 이미지 URL 또는 Base64 데이터 추출
    """
    # first_image_xpath='//*[@id="islrg"]/div[1]/div[1]/a[1]/div[1]/img'
    # first_image_xpath='//*[@id="cdx-image-0"]/div[2]/div/div/div/a[1]'
    #//*[@id="cdx-image-0"]/div[2]/div/div/div/a[1]
    # WebDriverWait(driver, 10).until(
    #     EC.visibility_of_element_located((By.XPATH, first_image_xpath))
    # )
    # driver.find_element(By.XPATH, first_image_xpath).click()
    images_xpath='//*[@id="cdx-image-0"]/div[2]/div/div/div/a'
    images=driver.find_elements(By.XPATH,images_xpath)
    image_urls = []

    for image in images[:num_images]:  # 최대 num_images 개수만큼 처리
        driver.execute_script('arguments[0].click();', image)
        time.sleep(3)  # 이미지 상세 페이지 로딩 대기

        try:
            detail_image_xpath = '//*[@id="cdx-image-0"]/div[2]/div/aside/div/header/div[1]/img'  # 상세 이미지 클래스 업데이트 필요
            detail_image = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, detail_image_xpath))
            )
            image_url = re.sub(r'/\d+px-','/700px-',detail_image.get_attribute('src'))
            print(image_url)
            if image_url.startswith('http') or 'data:image' in image_url:
                if 'data:image' in image_url:
                    # base64 인코딩된 이미지 데이터를 처리
                    header, encoded = image_url.split(",", 1)
                    image_urls.append(('base64', header + "," + encoded))
                else:
                    # 일반 URL
                    image_urls.append(('url', image_url))

        except Exception as e:
            print(f"{image_url}을 찾을 수 없습니다.")
            print(f"Error retrieving detail image: {e}")
            # 예외 발생 시 중단하지 않고 다음 이미지로 계속 진행
            continue

    return image_urls

# 이미지 다운로드를 위한 함수입니다.
def download_images(image_urls, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i, (data_type, data) in enumerate(image_urls):
        try:
            filename = f"image_{i + 1}"
            file_path = os.path.join(folder_path, filename)

            if data_type == 'url':
                # 일반 URL 이미지 처리
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                response = requests.get(data, headers=headers,stream=True)  # Use stream=True for efficient downloading
                if response.ok:  # Check if the request was successful
                    with open(f'{file_path}.jpg', "wb") as file:
                        for chunk in response.iter_content(chunk_size=128):  # Download the content in chunks
                            file.write(chunk)
                else:
                    print("Failed to download the image. Status code:", response.status_code)
            elif data_type == 'base64':
                # Base64 이미지 처리
                header, encoded = data.split(",", 1)
                image_data = base64.b64decode(encoded)
                with open(file_path + ".jpg", "wb") as file:
                    file.write(image_data)
        except Exception as e:
            print(f"Error downloading {data}: {e}")

def improve_image_quality(image_path, target_size=(640, 480)):
    """.
    이미지의 해상도를 변경하고, 선명도를 개선하며, 대비를 조정합니다.
    """
    # 이미지를 읽습니다.
    img = cv2.imread(image_path)

    # 이미지의 해상도를 변경합니다.
    resized_img = cv2.resize(img, target_size, interpolation=cv2.INTER_CUBIC)

    # 선명도를 개선하기 위한 커널을 생성합니다.
    kernel_sharpening = np.array([[-1, -1, -1],
                                  [-1, 9, -1],
                                  [-1, -1, -1]])

    # 커널을 적용하여 이미지에 선명도를 더합니다.
    sharpened_img = cv2.filter2D(resized_img, -1, kernel_sharpening)

    # 이미지의 대비를 조정합니다.
    lab = cv2.cvtColor(sharpened_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # 개선된 이미지를 저장합니다.
    cv2.imwrite(image_path, final_img)


# 개선된 이미지를 처리하고 원본을 삭제하는 함수입니다.
def process_images(folder_path, target_size=(640, 480)):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('jpg', 'jpeg', 'png')):
            image_path = os.path.join(folder_path, filename)
            # 이미지 품질 개선
            improve_image_quality(image_path, target_size)


def contains_korean(text):
    """
    Check if the text contains any Korean characters.
    Korean characters are in the Unicode range of 0xAC00 to 0xD7A3 for Hangul syllables.
    """
    return any('\uAC00' <= char <= '\uD7A3' for char in text)


def split_kor_eng(lines):
    """
    Splits lines into Korean and English parts, considering mixed languages and empty values.
    """
    korean_list = []
    english_list = []

    for line in lines:
        if not line.strip():  # Handle empty lines
            korean_list.append('')
            english_list.append('')
            continue

        korean_part = ''
        english_part = ''

        words = line.split(' ')
        for word in words:
            if contains_korean(word):
                korean_part += word + ' '
            else:
                english_part += word + ' '

        korean_list.append(korean_part.strip())
        english_list.append(english_part.strip())

    return korean_list, english_list


def main():
    df = pd.read_csv('data.csv', encoding='utf-8-sig')
    queries = df['명소 이름'].values.tolist()
    kor_queries, eng_queries=split_kor_eng(queries)
    num_images = 100


    for search_query in eng_queries:

        driver = chrome_driver()
        search_images(driver, search_query)
        scroll_page(driver)
        image_urls = collect_image_urls(driver, num_images)
        driver.quit()

        # 각 명소 이름으로 폴더 생성 및 이미지 저장
        folder_path = os.path.join('images', search_query.replace(' ', '_'))
        download_images(image_urls, folder_path)

        # 이미지 품질 개선 및 원본 이미지 삭제
        # process_images(folder_path)

        print(f"{len(os.listdir(folder_path))} images processed for {search_query}.")


if __name__ == "__main__":
    main()


