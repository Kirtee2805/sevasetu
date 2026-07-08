import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    service_account = json.loads(
        st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    )

    cred = credentials.Certificate(service_account)

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": st.secrets["FIREBASE_DATABASE_URL"]
        }
    )

root = db.reference("/")