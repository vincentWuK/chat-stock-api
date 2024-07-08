from fastapi import HTTPException, Request, Response, status, Depends, BackgroundTasks, APIRouter
from fastapi.responses import JSONResponse
from utils import query_news_by_tickers


router = APIRouter(tags=["sentiment"])


@router.get("/news/{tickers}")
async def fetch_ticker_news(
    tickers: str
):
    tickers = [ticker.strip() for ticker in tickers.split(',') if ticker.strip()]
    result = await query_news_by_tickers(tickers)
    return result