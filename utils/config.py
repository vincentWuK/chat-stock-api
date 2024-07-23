import os
from .logging import logger

BASE_PREFIX = os.getenv("BASE_PREFIX","/api")
PORT = int(os.getenv("PORT"))

API_PROVIDER_SUPPORTED = {"ALPHA_VANTAGE": "https://www.alphavantage.co/query"}


API_PROVIDER_SUPPORTED_EXTRA_PARAMS = {"ALPHA_VANTAGE": {"function": "NEWS_SENTIMENT"}}

API_PROVIDER_SUPPORTED_API_KEYS = {"ALPHA_VANTAGE": os.getenv("ALPHA_VANTAGE_API_KEY", "")}
NEWS_DB = os.getenv("NEWS_DB", "")
DB_CONFIG = {
        'host': os.getenv("POSTGRES_HOST", ""),
        'port': int(os.getenv("POSTGRES_PORT", 8080)),
        'user': os.getenv("POSTGRES_USERNAME", ""),
        'password': os.getenv("POSTGRES_PASSWORD", ""),
        'database': os.getenv("POSTGRES_DATABASE", ""),
    }
APIKEYS = [{"secret":os.getenv("SECRET", ""),"expired":os.getenv("EXPIRED", "")}]
CTRADER_CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
CTRADER_CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
CTRADER_ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
CTRADER_ACCOUNT_ID = int(os.getenv("CTRADER_ACCOUNT_ID"))
CTRADER_HOST_TYPE = os.getenv("CTRADER_HOST_TYPE")  # demo/live