import configparser
import json
import requests
from tqdm import tqdm 
from datetime import datetime

class VK:
    def __init__(self, token):
        self.token = token

    def get_photos(self, user_id, count=5):
        url = "https://api.vk.com/method/photos.get"
        params = {
            "owner_id": user_id,
            "album_id": "profile",
            "extended": 1,
            "photo_sizes": 1,
            "count": count,
            "access_token": self.token,
            "v": "5.131"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print("Ошибка при получении данных из VK.")
            return []

        data = response.json()
        if "error" in data:
            print(f"VK API error: {data['error']['error_msg']}")
            return []

        photos = []
        for item in data["response"]["items"]:
            max_size_photo = max(item["sizes"], key=lambda x: x["width"] * x["height"])
            likes = item["likes"]["count"]
            date = datetime.fromtimestamp(item["date"]).strftime('%Y-%m-%d')
            file_name = f"{likes}.jpg"
            if any(photo["file_name"] == file_name for photo in photos):
                file_name = f"{likes}_{date}.jpg"
            photos.append({
                "file_name": file_name,
                "size": max_size_photo["type"],
                "url": max_size_photo["url"]
            })
        return photos


class YD:
    def __init__(self, token):
        self.token = token

    def create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = {"Authorization": f"OAuth {self.token}"}
        params = {"path": folder_name}
        response = requests.put(url, headers=headers, params=params)
        if response.status_code not in [200, 201, 409]:
            print(f"Ошибка при создании папки: {response.json()}")
            return False
        return True

    def upload_file(self, folder_name, file_name, file_url):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {"Authorization": f"OAuth {self.token}"}
        params = {"path": f"{folder_name}/{file_name}", "url": file_url}
        response = requests.post(url, headers=headers, params=params)
        if response.status_code != 202:
            print(f"Ошибка при загрузке файла {file_name}: {response.json()}")
            return False
        return True


def main():
    config = configparser.ConfigParser()
    config.read("settings.ini")
    vk_token = config["Tokens"]["vk_token"]
    yd_token = config["Tokens"]["yd_token"]

    vk = VK(vk_token)
    yd = YD(yd_token)

    user_id = input("Введите ID пользователя VK: ")
    photo_count = int(input("Введите количество фотографий для загрузки (по умолчанию 5): ") or 5)

    print("Получение фотографий из VK...")
    photos = vk.get_photos(user_id, count=photo_count)

    if not photos:
        print("Не удалось получить фотографии.")
        return

    folder_name = f"vk_profile_photos_{user_id}"
    print(f"Создание папки '{folder_name}' на Яндекс.Диске...")
    if not yd.create_folder(folder_name):
        print("Не удалось создать папку на Яндекс.Диске.")
        return

    print("Загрузка фотографий на Яндекс.Диск...")
    photos_data = []
    for photo in tqdm(photos, desc="Загрузка", unit="фото"):
        if yd.upload_file(folder_name, photo["file_name"], photo["url"]):
            photos_data.append({
                "file_name": photo["file_name"],
                "size": photo["size"]
            })

    with open("uploaded_photos.json", "w", encoding="utf-8") as f:
        json.dump(photos_data, f, ensure_ascii=False, indent=4)

    print("Фотографии успешно загружены на Яндекс.Диск. Информация сохранена в uploaded_photos.json.")


if __name__ == "__main__":
    main()