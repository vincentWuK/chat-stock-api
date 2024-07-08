from fastapi import HTTPException, Request, Response, status, Depends, BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
import aiohttp
import asyncio

from utils import logger
from utils import API_PROVIDER_SUPPORTED, API_PROVIDER_SUPPORTED_EXTRA_PARAMS, API_PROVIDER_SUPPORTED_API_KEYS
from utils import insert_news


router = APIRouter(tags=["news"])


async def fetch_news(base_url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            data = await response.json()
        logger.debug(params)
    return data


@router.get("/news/update/{tickers}")
async def fetch_all_news(
    tickers: str
):
    '''
    This api is used to update news of specific tickers
    '''
    for provider in API_PROVIDER_SUPPORTED.keys():
        base_url = API_PROVIDER_SUPPORTED[provider]
        params = API_PROVIDER_SUPPORTED_EXTRA_PARAMS[provider]
        api_key = API_PROVIDER_SUPPORTED_API_KEYS[provider]
        tickers = [ticker.strip() for ticker in tickers.split(',') if ticker.strip()]

        for ticker in tickers:
            temp_params = params
            temp_params.update({"tickers":ticker, "apikey":api_key})
            try:      
                data = await fetch_news(base_url, temp_params)
                for news_item in data['feed']:
                    await insert_news(news_item)

                logger.info(f"Update ticker data for {ticker} successfully")
            except Exception as e:
                logger.error(f"News update for ticker {ticker} error, Except: {e}", exc_info=True)
        
        return JSONResponse(status_code=200, content={"message": "OK"})
    
    
