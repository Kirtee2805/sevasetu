import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

if not firebase_admin._apps:
    cred = credentials.Certificate(
        dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
    )
    firebase_admin.initialize_app(cred, {
        "databaseURL": st.secrets["FIREBASE_DATABASE_URL"]
    })

root = db.reference("/")