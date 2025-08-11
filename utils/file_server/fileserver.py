import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:9000")

def generate_download_link(category: str, file_name: str) -> str | None:
    file_path = os.path.join("data_sources", category, file_name)
    if os.path.exists(file_path):
        return f"{BASE_URL}/data_sources/{category}/{file_name}"
    return None
