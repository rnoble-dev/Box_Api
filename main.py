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
        print('Getting New Files From Upload Automation Folder ......')
        items = self.client.folder(folder_id=self.main_folder).get_items()
        for item in items:
            if item.type == 'file':
                self.create_folders_and_move_files_from_main(item.name, item.id)

    def get_all_files_sub_dir(self):
        print('Getting New Files From Upload Automation Sub Folders ......')
        items = self.client.folder(folder_id=self.main_folder).get_items()
        for item in items:
            if item.type == 'folder':
                sub_folder = self.client.folder(folder_id=item.id).get_items()
                for obj in sub_folder:
                    if obj.type == 'file':
                        self.create_folders_and_move_files_from_sub(item.name, obj.name, obj.id)

    def create_folders_and_move_files_from_main(self, file_name, file_id):
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
            if folder_name not in folder_name_list:
                create_folder = self.client.folder(self.client_folder).create_subfolder(folder_name)
                file_to_move = self.client.file(file_id)
                destination_folder = self.client.folder(create_folder.id)
                file_to_move.move(destination_folder, name=file__name)
            else:
                print('Downloading Duplicate Pdf ......')
                if not os.path.exists('file.pdf'):
                    open('file.pdf', 'w')
                output_file = open(self.duplicate_pdf, 'wb')
                self.client.file(file_id).download_to(output_file)
                self.upload_new_version_from_main_folder(file_name, file_id)

    def create_folders_and_move_files_from_sub(self, sub_folder_name, file_name, file_id):
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
            if len(sub_folder_name) > 0:
                folder_name = file_name.split('---')[0]
                file__name = file_name.split('---')[1]
                if folder_name not in folder_name_list:
                    create_folder = self.client.folder(self.client_folder).create_subfolder(folder_name)
                    sub_folder = self.client.folder(create_folder.id).create_subfolder(sub_folder_name)
                    file_to_move = self.client.file(file_id)
                    destination_folder = self.client.folder(sub_folder.id)
                    file_to_move.move(destination_folder, name=file__name)
                else:
                    print('Downloading Duplicate Pdf ......')
                    if not os.path.exists('file.pdf'):
                        open('file.pdf', 'w')
                    output_file = open(self.duplicate_pdf, 'wb')
                    self.client.file(file_id).download_to(output_file)
                    self.upload_new_version_from_sub_folder(sub_folder_name, file_name, file_id)

    def upload_new_version_from_main_folder(self, file_name, file_id):
        print('Checking Version of File in Client Folder ......')
        folder_name = file_name.split('---')[0]
        file__name = file_name.split('---')[1]
        client_folder = self.client.folder(folder_id=self.client_folder).get_items()
        folder_obj = [f"{folder.id},{folder.name}" for folder in client_folder]
        for obj in folder_obj:
            folder_id = obj.split(',')[0]
            folder__name = obj.split(',')[1]
            if folder_name == folder__name:
                content = self.client.folder(folder_id=folder_id).get_items()
                filename = [file.name for file in content]
                files = self.client.folder(folder_id=folder_id).get_items()
                if not filename:
                    file_to_move = self.client.file(file_id)
                    destination_folder = self.client.folder(folder_id)
                    file_to_move.move(destination_folder, name=file__name)
                    os.remove('file.pdf')
                else:
                    for file in files:
                        if file.type == 'file':
                            if file__name == file.name:
                                print('UPDATING VERSION OF FILE FOR ..' + file__name)
                                stream = open(self.duplicate_pdf, 'rb')
                                self.client.file(file.id).update_contents_with_stream(stream)
                                self.client.file(file_id=file_id).delete()
                                os.remove('file.pdf')
                        if file__name not in filename:
                            print('ADDING ' + file__name + ' to folder')
                            file_to_move = self.client.file(file_id)
                            destination_folder = self.client.folder(folder_id)
                            file_to_move.move(destination_folder, name=file__name)
                            filename.append(file__name)
                            os.remove('file.pdf')

    def upload_new_version_from_sub_folder(self, sub_folder_name, file_name, file_id):
        print('Checking Version of File in Client Sub Folder ......')
        folder_name = file_name.split('---')[0]
        file__name = file_name.split('---')[1]
        client_folder = self.client.folder(folder_id=self.client_folder).get_items()
        folder_obj = [f"{folder.id},{folder.name}" for folder in client_folder]
        for obj in folder_obj:
            folder_id = obj.split(',')[0]
            folder__name = obj.split(',')[1]
            if folder_name == folder__name:
                contents = self.client.folder(folder_id=folder_id).get_items()
                content_name = [content.name for content in contents]
                folders_files = self.client.folder(folder_id=folder_id).get_items()
                if not content_name:
                    create_sub_folder = self.client.folder(folder_id).create_subfolder(sub_folder_name)
                    file_to_move = self.client.file(file_id)
                    destination_folder = self.client.folder(create_sub_folder.id)
                    file_to_move.move(destination_folder, name=file__name)
                    os.remove('file.pdf')
                else:
                    for item in folders_files:
                        if sub_folder_name in content_name:
                            if sub_folder_name == item.name:
                                sub__folder = self.client.folder(folder_id=item.id).get_items()
                                for file in sub__folder:
                                    if file__name == file.name:
                                        print('UPDATING VERSION OF FILE FOR ..' + file__name + 'IN SUB FOLDER')
                                        stream = open(self.duplicate_pdf, 'rb')
                                        self.client.file(file.id).update_contents_with_stream(stream)
                                        self.client.file(file_id=file_id).delete()
                                        os.remove('file.pdf')
                        if sub_folder_name not in content_name:
                            print('CREATING SUB FOLDER AND ADDING FILE ' + file__name)
                            create_sub_folder = self.client.folder(folder_id).create_subfolder(sub_folder_name)
                            file_to_move = self.client.file(file_id)
                            destination_folder = self.client.folder(create_sub_folder.id)
                            file_to_move.move(destination_folder, name=file__name)
                            content_name.append(sub_folder_name)
                            os.remove('file.pdf')


if __name__ == '__main__':
    main = APIConnect()
    main.get_all_folder_ids()
    main.get_all_files_sub_dir()
