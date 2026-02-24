import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 's)m3R@nd0mC0d3!'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'postgresql://azadmin:PassJP10%40@justpick-db.postgres.database.azure.com:5432/agriecodb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PREFIX = '/api'
    UPLOAD_FOLDER = 'app/public/uploads'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    # HOST = 'https://agrieco-connect-be.azurewebsites.net'
