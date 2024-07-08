import os


BASE_PREFIX = os.getenv("BASE_PREFIX")
PORT = int(os.getenv("PORT"))

API_PROVIDER_SUPPORTED = {"ALPHA_VANTAGE": "https://www.alphavantage.co/query"}


API_PROVIDER_SUPPORTED_EXTRA_PARAMS = {"ALPHA_VANTAGE": {"function": "NEWS_SENTIMENT"}}

API_PROVIDER_SUPPORTED_API_KEYS = {"ALPHA_VANTAGE": os.getenv("ALPHA_VANTAGE_API_KEY")}
NEWS_DB = os.getenv("NEWS_DB")
DB_CONFIG = {
        'host': os.getenv("POSTGRES_HOST"),
        'port': int(os.getenv("POSTGRES_PORT")),
        'user': os.getenv("POSTGRES_USERNAME"),
        'password': os.getenv("POSTGRES_PASSWORD"),
        'database': os.getenv("POSTGRES_DB"),
    }
