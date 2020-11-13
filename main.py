import os
import time
import urllib.parse as urlparse
from urllib.parse import parse_qs
from boxsdk import Client, OAuth2
from dotenv import load_dotenv
from selenium import webdriver

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
        self.main_folder = ''
        self.main_error_folder = ''
        self.client_folder = ''
        self.sub_folder_name = ''
        self.duplicate_pdf = (
            f"{os.path.dirname(os.path.abspath(__file__))}/file.pdf"
        )

    def get_access_token(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome('./chromedriver', options=chrome_options)
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
        return client

    def get_all_folder_ids(self):
        print('Getting Folder Information ......')
        fin_folio = ''
        root_folder = self.client.root_folder().get_items()
        for items in root_folder:
            if "Upload Automation" in items.name:
                self.main_folder = items.id
            if "Upload Error Files" in items.name:
                self.main_error_folder = items.id
            if "Finfolio" in items.name:
                fin_folio = items.id
        fin_folio_folder = self.client.folder(folder_id=fin_folio).get_items()
        for items in fin_folio_folder:
            if "Client" in items.name:
                self.client_folder = items.id
        self.get_all_files_main_dir()

    def get_all_files_main_dir(self):
        print('Getting New Files ......')
        items = self.client.folder(folder_id=self.main_folder).get_items()
        for item in items:
            if item.type == 'file':
                self.create_folders_and_move_files(item.name, item.id)
            if item.type == 'folder':
                sub_folder = self.client.folder(folder_id=item.id).get_items()
                for obj in sub_folder:
                    self.sub_folder_name = item.name
                    if obj.type == 'file':
                        self.create_folders_and_move_files(obj.name, obj.id)

    def create_folders_and_move_files(self, file_name, file_id):
        full_file_name = file_name
        main_error_folder = self.client.folder(folder_id=self.main_error_folder).get_items()
        client_folder = self.client.folder(folder_id=self.client_folder).get_items()
        faulty_file_name_list = [file.name for file in main_error_folder]
        folder_name_list = [folder.name for folder in client_folder]
        if '---' not in full_file_name:
            if full_file_name not in faulty_file_name_list:
                file_to_move = self.client.file(file_id)
                destination_folder = self.client.folder(self.main_error_folder)
                file_to_move.move(destination_folder)
            else:
                self.client.file(file_id=file_id).delete()
        else:
            folder_name = file_name.split('---')[0]
            file__name = file_name.split('---')[1]
            if len(self.sub_folder_name) > 0:
                if folder_name not in folder_name_list:
                    create_folder = self.client.folder(self.client_folder).create_subfolder(folder_name)
                    sub_folder = self.client.folder(create_folder.id).create_subfolder(self.sub_folder_name)
                    file_to_move = self.client.file(file_id)
                    destination_folder = self.client.folder(sub_folder.id)
                    file_to_move.move(destination_folder, name=file__name)
                else:
                    self.download_duplicate_file(file_name, file_id)
            else:
                if folder_name not in folder_name_list:
                    create_folder = self.client.folder(self.client_folder).create_subfolder(folder_name)
                    file_to_move = self.client.file(file_id)
                    destination_folder = self.client.folder(create_folder.id)
                    file_to_move.move(destination_folder, name=file__name)
                else:
                    self.download_duplicate_file(file_name, file_id)

    def download_duplicate_file(self, file_name, file_id):
        print('Downloading Duplicate Pdf ......')
        if not os.path.exists('file.pdf'):
            open('file.pdf', 'w')
        output_file = open(self.duplicate_pdf, 'wb')
        self.client.file(file_id).download_to(output_file)
        self.upload_new_version_existing_file(file_name, file_id)

    def upload_new_version_existing_file(self, file_name, file_id):
        print('Checking Version of File ......')
        folder_name = file_name.split('---')[0]
        file__name = file_name.split('---')[1]
        client_folder = self.client.folder(folder_id=self.client_folder).get_items()
        folder_obj = [f"{folder.id},{folder.name}" for folder in client_folder]
        for obj in folder_obj:
            folder_id = obj.split(',')[0]
            folder__name = obj.split(',')[1]
            if folder_name == folder__name:
                folders_files = self.client.folder(folder_id=folder_id).get_items()
                item_name_list = [item.name for item in folders_files]
                items = self.client.folder(folder_id=folder_id).get_items()
                for item in items:
                    if len(self.sub_folder_name) > 0:
                        if item.type == 'folder':
                            if self.sub_folder_name == item.name:
                                sub_folder = self.client.folder(folder_id=item.id).get_items()
                                file_obj = [f"{file.id},{file.name}" for file in sub_folder]
                                for file in file_obj:
                                    filename = file.split(',')[1]
                                    fileid = file.split(',')[0]
                                    if file__name == filename:
                                        stream = open(self.duplicate_pdf, 'rb')
                                        self.client.file(fileid).update_contents_with_stream(stream)
                                        self.client.file(file_id=file_id).delete()
                                        os.remove('file.pdf')
                            else:
                                if self.sub_folder_name not in item_name_list:
                                    create_sub_folder = self.client.folder(folder_id).create_subfolder(
                                        self.sub_folder_name)
                                    file_to_move = self.client.file(file_id)
                                    destination_folder = self.client.folder(create_sub_folder.id)
                                    file_to_move.move(destination_folder, name=file__name)
                                    item_name_list.append(self.sub_folder_name)
                        else:
                            if self.sub_folder_name not in item_name_list:
                                create_sub_folder = self.client.folder(folder_id).create_subfolder(self.sub_folder_name)
                                file_to_move = self.client.file(file_id)
                                destination_folder = self.client.folder(create_sub_folder.id)
                                file_to_move.move(destination_folder, name=file__name)
                                item_name_list.append(self.sub_folder_name)
                    else:
                        for file in items:
                            if file__name == file.name:
                                stream = open(self.duplicate_pdf, 'rb')
                                self.client.file(file.id).update_contents_with_stream(stream)
                                self.client.file(file_id=file_id).delete()
                                os.remove('file.pdf')


if __name__ == '__main__':
    main = APIConnect()
    main.get_all_folder_ids()
