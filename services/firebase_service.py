import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:

    cred = credentials.Certificate("firebase_credential.json")

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://sevasetu-70378-default-rtdb.firebaseio.com"
        }
    )

root = db.reference("/")