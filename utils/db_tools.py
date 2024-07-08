import json
import asyncpg
from datetime import datetime

from .config import NEWS_DB, DB_CONFIG
from .logging import logger


async def insert_news(news_item):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        async with conn.transaction():
            sql = f"""
            INSERT INTO "{NEWS_DB}" (
                title, url, "timePublished", authors, summary, "bannerImage", 
                source, "categoryWithinSource", "sourceDomain", topics, 
                "overallSentimentScore", "overallSentimentLabel", "tickerSentiment"
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            """
            values = (
                news_item['title'],
                news_item['url'],
                datetime.strptime(news_item['time_published'], '%Y%m%dT%H%M%S'),
                json.dumps(news_item['authors']),
                news_item['summary'],
                news_item['banner_image'],
                news_item['source'],
                news_item['category_within_source'],
                news_item['source_domain'],
                json.dumps(news_item['topics']),
                news_item['overall_sentiment_score'],
                news_item['overall_sentiment_label'],
                json.dumps(news_item['ticker_sentiment'])
            )
            await conn.execute(sql, *values)
    finally:
        await conn.close()

async def query_news_by_tickers(tickers):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        async with conn.transaction():
            ticker_conditions = " OR ".join([
                f"EXISTS (SELECT 1 FROM jsonb_array_elements(\"tickerSentiment\") AS item WHERE item->>'ticker' = ${i+1})"
                for i in range(len(tickers))
            ])
            
            sql = f"""
            SELECT * FROM "{NEWS_DB}"
            WHERE {ticker_conditions}
            ORDER BY "timePublished" DESC
            """
            
            logger.debug(f"Executing SQL: {sql}")
            logger.debug(f"Parameters: {tickers}")
            
            rows = await conn.fetch(sql, *tickers)
            
            if not rows:
                logger.warning("Query returned no results.")
                sample_sql = f"""
                SELECT "tickerSentiment" FROM "{NEWS_DB}"
                LIMIT 1
                """
                sample = await conn.fetchval(sample_sql)
                logger.debug(f"Sample tickerSentiment: {sample}")
            
            processed_results = []
            for row in rows:
                processed_row = dict(row)
                for field in ['authors', 'topics', 'tickerSentiment']:
                    if isinstance(processed_row[field], str):
                        try:
                            processed_row[field] = json.loads(processed_row[field])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON for field {field}")
                processed_results.append(processed_row)
            
            logger.info(f"Processed {len(processed_results)} results")
            
            return processed_results
    finally:
        await conn.close()