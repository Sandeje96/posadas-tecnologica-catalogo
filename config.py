import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///posadas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS

    # Fix for postgres:// or postgresql:// (Railway uses postgres:// or postgresql://)
    @staticmethod
    def fix_database_url(url):
        if not url:
            return url
        if url.startswith('postgres://'):
            return url.replace('postgres://', 'postgresql+psycopg2://', 1)
        if url.startswith('postgresql://'):
            return url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return url

    def __init__(self):
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///posadas.db')
        self.SQLALCHEMY_DATABASE_URI = Config.fix_database_url(db_url)
