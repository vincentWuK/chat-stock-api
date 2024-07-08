import asyncpg

from fastapi import FastAPI
from contextlib import asynccontextmanager

from routers.sentiment_router import router as sentiment_router
from routers.news_router import router as news_router
from utils import BASE_PREFIX, PORT, DB_CONFIG
from utils import logger


async def init_db_pool():
    return await asyncpg.create_pool(
        database=DB_CONFIG["db"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        min_size=0,
        max_size=2
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init
    #try:
    #    app.state.db_pool = await init_db_pool()
    #except Exception as e:
    #    logger.error(f"Init db pool error, Except: {e}", exc_info=True)
    app.state.task_status = {}
    yield
    #await app.state.db_pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(sentiment_router, prefix=BASE_PREFIX)
app.include_router(news_router, prefix=BASE_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)  # dev 6003, test 6002, prod 6001
