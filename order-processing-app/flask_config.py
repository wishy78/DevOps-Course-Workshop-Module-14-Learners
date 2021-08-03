import os
import pyodbc
import urllib
import random

connect_string = f"Driver={{{pyodbc.drivers()[-1]}}};Server=tcp:{os.environ.get('DB_SERVER_NAME')},1433;Database={os.environ.get('DATABASE_NAME')};Uid={os.environ.get('DATABASE_USER')};Pwd={os.environ.get('DATABASE_PASSWORD')};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
url_encoded_connect_string = urllib.parse.quote_plus(connect_string)

class Config:
    INSTANCE_ID = os.environ.get("INSTANCE_ID", str(random.randint(100000, 999999)))
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={url_encoded_connect_string}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULED_JOB_INTERVAL_SECONDS = int(os.environ.get('SCHEDULED_JOB_INTERVAL_SECONDS'))
    SCHEDULED_JOB_MAX_INSTANCES = int(os.environ.get('SCHEDULED_JOB_MAX_INSTANCES'))
    SCHEDULED_JOB_ENABLED = os.environ.get('SCHEDULED_JOB_ENABLED', 'true').lower() != 'false'
    FINANCE_PACKAGE_URL = os.environ.get('FINANCE_PACKAGE_URL')
    IMAGE_OUTPUT_FOLDER = os.environ.get("IMAGE_OUTPUT_FOLDER", "output_images")
