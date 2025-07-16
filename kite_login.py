from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

def get_kite_instance():
    api_key = os.getenv("API_KEY")
    access_token = os.getenv("ACCESS_TOKEN")

    if not api_key or not access_token:
        raise Exception("Missing API_KEY or ACCESS_TOKEN in .env file")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
