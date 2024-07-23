from datetime import datetime
from utils import logger, APIKEYS

async def verify(secret: str):
    for valid_user in APIKEYS:
        if valid_user["secret"] == secret:
            if valid_user.expiration > datetime.utcnow():
                logger.info("Valid key, Start trading!")
                return True, None
            else:
                msg = "Secret expired, plz generate a new one."
                logger.info(msg)
                return False, msg
    msg = "Invalid Key, Plz check your key"
    logger.info(msg)
    return False, msg