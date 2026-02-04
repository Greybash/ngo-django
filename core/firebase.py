import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings
import os

cred_path = os.path.join(settings.BASE_DIR, "firebase-service-account.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
