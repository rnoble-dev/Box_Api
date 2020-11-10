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
        self.duplicate_pdf = (
            f"{os.path.dirname(os.path.abspath(__file__))}/file.pdf"
        )

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

    def get_all_folder_ids(self):
        upload_folder_id = ''
        upload_error_folder_id = ''
        fin_folio = ''
        client = ''
        root_folder = self.client.root_folder().get_items()
        for items in root_folder:
            if "Upload Automation" in items.name:
                upload_folder_id = items.id
            if "Finfolio" in items.name:
                fin_folio = items.id
        fin_folio_folder = self.client.folder(folder_id=fin_folio).get_items()
        for items in fin_folio_folder:
            if "Upload Automation Errors" in items.name:
                upload_error_folder_id = items.id
            if "Client" in items.name:
                client = items.id
        self.get_files_in_main_folder_create_folders_move_files(upload_folder_id, upload_error_folder_id, client)

    def get_files_in_main_folder_create_folders_move_files(self, upload_folder_id, upload_error_folder_id,
                                                           client_folder_id):
        error_folder = self.client.folder(folder_id=upload_error_folder_id).get_items()
        client_folder = self.client.folder(folder_id=client_folder_id).get_items()
        items = self.client.folder(folder_id=upload_folder_id).get_items()
        error_file_names = [file.name for file in error_folder]
        folder_name = [folder.name for folder in client_folder]
        for item in items:
            if item.type == 'file':
                if '---' not in item.name:
                    if item.name not in error_file_names:
                        file_to_move = self.client.file(item.id)
                        destination_folder = self.client.folder(upload_error_folder_id)
                        file_to_move.move(destination_folder)
                else:
                    if item.name.split('---')[0] not in folder_name:
                        new_folder = self.client.folder(client_folder_id).create_subfolder(item.name.split('---')[0])
                        file_to_move = self.client.file(item.id)
                        destination_folder = self.client.folder(new_folder.id)
                        file_to_move.move(destination_folder, name=item.name.split('---')[1])
                    else:
                        self.download_duplicate_file(item, client_folder_id)
            if item.type == 'folder':
                self.get_files_sub_folders_create_folders_move_files(item.id, client_folder_id, upload_error_folder_id)

    def get_files_sub_folders_create_folders_move_files(self, folder_id, client_folder_id, upload_error_folder_id):
        error_folder = self.client.folder(folder_id=upload_error_folder_id).get_items()
        client_folder = self.client.folder(folder_id=client_folder_id).get_items()
        items = self.client.folder(folder_id=folder_id).get_items()
        error_file_names = [file.name for file in error_folder]
        folder_name = [folder.name for folder in client_folder]
        for item in items:
            if item.type == 'file':
                if '---' not in item.name:
                    if item.name not in error_file_names:
                        file_to_move = self.client.file(item.id)
                        destination_folder = self.client.folder(upload_error_folder_id)
                        file_to_move.move(destination_folder)
                else:
                    if item.name.split('---')[0] not in folder_name:
                        new_folder = self.client.folder(client_folder_id).create_subfolder(item.name.split('---')[0])
                        file_to_move = self.client.file(item.id)
                        destination_folder = self.client.folder(new_folder.id)
                        file_to_move.move(destination_folder, name=item.name.split('---')[1])
                    else:
                        self.download_duplicate_file(item, client_folder_id)

    def download_duplicate_file(self, item, client_folder_id):
        if not os.path.exists('file.pdf'):
            open('file.pdf', 'w')
        output_file = open(self.duplicate_pdf, 'wb')
        self.client.file(item.id).download_to(output_file)
        self.upload_new_version_existing_file(item, client_folder_id)

    def upload_new_version_existing_file(self, item, client_folder_id):
        client_folder = self.client.folder(folder_id=client_folder_id).get_items()
        folder_name = [f"{folder.id},{folder.name}" for folder in client_folder]
        for folder_stats in folder_name:
            format_name = folder_stats.split(',')
            if item.name.split('---')[0] == format_name[1]:
                files = self.client.folder(folder_id=format_name[0]).get_items()
                for file in files:
                    if item.name.split('---')[1] == file.name:
                        stream = open(self.duplicate_pdf, 'rb')
                        self.client.file(file.id).update_contents_with_stream(stream)
                        self.client.file(file_id=item.id).delete()
                        os.remove('file.pdf')


if __name__ == '__main__':
    main = APIConnect()
    main.get_access_token()
    main.get_all_folder_ids()
