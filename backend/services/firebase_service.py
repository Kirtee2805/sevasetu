import firebase_admin
from firebase_admin import credentials, db
import random

# Initialize Firebase (Checks if already initialized to avoid errors)
if not firebase_admin._apps:
    # Ensure this points to where you saved your JSON key
    cred = credentials.Certificate("firebase_credential.json")
    firebase_admin.initialize_app(cred, {
        # IMPORTANT: Replace this with your actual Realtime Database URL
        'databaseURL': 'https://sevasetu-70378-default-rtdb.firebaseio.com/' 
    })

# ==========================================
# CRUD OPERATIONS
# ==========================================

def save_phc_data(data: dict):
    """Saves a new PHC record to Firebase."""
    ref = db.reference('phc_records')
    # Use the generated record_id as the child node key
    ref.child(data['record_id']).set(data)
    return data

def get_all_phc_data() -> dict:
    """Retrieves all PHC records from Firebase."""
    ref = db.reference('phc_records')
    records = ref.get()
    # Return empty dict if no records exist yet
    return records if records else {}

def update_record(record_id: str, data: dict):
    """Updates an existing PHC record."""
    ref = db.reference(f'phc_records/{record_id}')
    ref.update(data)
    return data

def delete_record(record_id: str):
    """Deletes a PHC record."""
    ref = db.reference(f'phc_records/{record_id}')
    ref.delete()
    return True

# ==========================================
# INTELLIGENCE & ANALYTICS (Mocked for UI)
# ==========================================

import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase using Google Cloud's built-in security
if not firebase_admin._apps:
    # Use ApplicationDefault() instead of the JSON file!
    cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred, {
        # Keep your actual database URL here
        'databaseURL': 'https://sevasetu-70378-default-rtdb.firebaseio.com/' 
    })