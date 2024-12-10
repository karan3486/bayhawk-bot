import os
# from dotenv import load_dotenv

# load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ASTRA_DB_TOKEN = os.getenv('ASTRA_DB_TOKEN')
    ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    ADMISSION_TEAM = os.getenv("ADMISSION_TEAM")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    RESULTS_FOLDER = os.getenv("RESULTS_FOLDER")
    ALLOWED_EXTENSIONS= os.getenv("ALLOWED_EXTENSIONS")
