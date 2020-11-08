from boxsdk import Client, OAuth2
from dotenv import load_dotenv
from selenium import webdriver
import urllib.parse as urlparse
from urllib.parse import parse_qs
import time
import os

load_dotenv()
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URL_ = os.environ.get("REDIRECT_URL")
LOGIN = os.environ.get("LOGIN")
PASSWORD = os.environ.get("PASSWORD")


class APIConnect:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_url = REDIRECT_URL_
        self.login = LOGIN
        self.password = PASSWORD
        self.client = self.get_access_token()
        self.files = []

    def get_access_token(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)
        sdk = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        REDIRECT_URL = f'https://account.box.com/api/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.redirect_url}&response_type=code'
        driver.get(REDIRECT_URL)
        driver.find_element_by_id('login').send_keys(self.login)
        driver.find_element_by_id('password').send_keys(self.password)
        driver.find_element_by_class_name('login_submit').click()
        time.sleep(1)
        driver.find_element_by_class_name('submit').click()
        time.sleep(1)
        url = driver.current_url
        parsed = urlparse.urlparse(url)
        auth_url = parse_qs(parsed.query)['code'][0]
        driver.close()
        access_token, refresh_token = sdk.authenticate(auth_url)
        oauth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=access_token,
            refresh_token=refresh_token
        )
        client = Client(oauth)
        # user = client.user().get()
        return client

    def sort_and_return_all_files(self):
        upload_folder_id = ''
        sub_folders = []
        root_folder = self.client.root_folder().get_items()
        for items in root_folder:
            if "Upload Automation" in items.name:
                upload_folder_id = items.id
        items = self.client.folder(folder_id=upload_folder_id).get_items()
        for item in items:
            if item.type == 'file':
                self.files.append(f"{item.id}---{item.name}")
            if item.type == 'folder':
                sub_folders.append(item.id)
        for folder_id in sub_folders:
            items = self.client.folder(folder_id=folder_id).get_items()
            file_names = [f"{item.id}---{item.name}" for item in items]
            self.files.extend(file_names)

    def get_folder_id_for_file_placement(self):
        fin_folio_folder_id = ''
        client_folder_id = ''
        root_folder = self.client.root_folder().get_items()
        for info in root_folder:
            if "Finfolio" in info.name:
                fin_folio_folder_id = info.id
        items = self.client.folder(folder_id=fin_folio_folder_id).get_items()
        for item in items:
            if "Client" in item.name:
                client_folder_id = item.id
        self.create_new_folders(client_folder_id)
        return client_folder_id

    def create_new_folders(self, client_folder_id):
        folders = self.client.folder(folder_id=client_folder_id).get_items()
        folder_name = [folder.name for folder in folders]
        for file in self.files:
            format_name = file.split('---')
            if format_name[1] not in folder_name:
                self.client.folder(client_folder_id).create_subfolder(format_name[1])
            self.sort_and_move_files(format_name, client_folder_id)

    def sort_and_move_files(self, file_name, client_folder):
        folders = self.client.folder(folder_id=client_folder).get_items()
        for folder in folders:
            if file_name[1] == folder.name:
                file_to_move = self.client.file(file_name[0])
                destination_folder = self.client.folder(folder.id)
                file_to_move.move(destination_folder, name=file_name[2])


if __name__ == '__main__':
    main = APIConnect()
    main.get_access_token()
    main.sort_and_return_all_files()
    main.get_folder_id_for_file_placement()
