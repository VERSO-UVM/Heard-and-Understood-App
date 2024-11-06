import firebase_admin
from firebase_admin import credentials


def initialize_firebase():
    # Point to the service account key file inside the firebase folder
    cred = credentials.Certificate('firebase/serviceAccountKey.json')
    firebase_admin.initialize_app(cred)
