import requests

url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Entire_roasted_chicken.jpg/700px-Entire_roasted_chicken.jpg'
response = requests.get(url, stream=True)  # Use stream=True for efficient downloading

if response.ok:  # Check if the request was successful
    with open('./images/turkey/image_1.jpg', "wb") as file:
        for chunk in response.iter_content(chunk_size=128):  # Download the content in chunks
            file.write(chunk)
else:
    print("Failed to download the image. Status code:", response.status_code)
