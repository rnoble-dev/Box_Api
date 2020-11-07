from boxsdk import Client, OAuth2
from dotenv import load_dotenv
import requests
import os


load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

class APIConnect:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.access_token = ACCESS_TOKEN

    def api_connect(self):
        auth = OAuth2(
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=self.access_token,
        )
        client = Client(auth)

        user = client.user().get()
        print('The current user ID is {0}'.format(user.id))
        root_folder = client.root_folder().get()
        for item in root_folder:
            print(item)

        items = client.folder(folder_id='125711645862').get_items()
        for item in items:
            print('{0} {1} is named "{2}"'.format(item.type.capitalize(), item.id, item.name))

if __name__ == '__main__':
    main = APIConnect()
    main.api_connect()