import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

    # Database Configuration
    MONGO_URI = os.environ.get("MONGO_URI") or "mongodb://localhost:27017/"
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME") or "technician_chatbot"

    # Perplexity API Configuration
    PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
    PERPLEXITY_API_URL = (
        os.environ.get("PERPLEXITY_API_URL")
        or "https://api.perplexity.ai/chat/completions"
    )
    PERPLEXITY_MODEL = os.environ.get("PERPLEXITY_MODEL") or "sonar-medium-online"

    # Admin Configuration
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "admin123"

    # Chatbot Configuration
    MAX_RESPONSE_LENGTH = int(os.environ.get("MAX_RESPONSE_LENGTH", 500))
    INTENT_CONFIDENCE_THRESHOLD = float(
        os.environ.get("INTENT_CONFIDENCE_THRESHOLD", 0.7)
    )

    # Logging Configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
