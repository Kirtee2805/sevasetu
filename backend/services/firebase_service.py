import firebase_admin
from firebase_admin import credentials, db
import streamlit as st
import json

# Check if the app is already initialized to avoid "already exists" errors
if not firebase_admin._apps:
    try:
        # Access the secret we added to Streamlit Cloud
        # Ensure the key name here matches exactly what you wrote in Secrets
        service_account_info = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        
        # Create the certificate object from the dictionary
        cred = credentials.Certificate(service_account_info)
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://sevasetu-70378-default-rtdb.firebaseio.com/' 
        })
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        st.stop()