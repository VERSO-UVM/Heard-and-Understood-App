import firebase_admin
from firebase_admin import credentials
from hua import FIREBASE_CREDS


def initialize_firebase():
    # Point to the service account key file inside the firebase folder
    cred = credentials.Certificate(FIREBASE_CREDS)
    firebase_admin.initialize_app(cred)
