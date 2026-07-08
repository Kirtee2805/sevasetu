import os
import json
import firebase_admin
from firebase_admin import credentials, db # Make sure to import 'db' here

# Fetch the JSON string from the environment variable
service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

if service_account_json and not firebase_admin._apps:
    try:
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
        
        # Initialize the app with the database URL
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://sevasetu-70378-default-rtdb.firebaseio.com/'
        })
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

# 'db' is now initialized and ready to be used by app.py