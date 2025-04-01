from utils import ShortURL, short_code_generator
import asyncio
import asyncpg

class Database:
    def __init__(self, config):
        self.config = config
        self.pool = None
        self.lock = asyncio.Lock()
    
    async def init_db(self):
        await self.create_pool()
        await self.create_table()

    async def create_pool(self):
        async with self.lock:
            if self.pool:
                return
            for _ in range(self.config.db_connect_retries):
                try:
                    self.pool = await asyncpg.create_pool(
                        user=self.config.db_user,
                        password=self.config.db_password,
                        database=self.config.db_name,
                        host=self.config.db_host,
                        port=self.config.db_port,
                        min_size=1,
                        max_size=10,
                    )
                    return
                except Exception as e:
                    print(f"Database connection failed: {e}. Retrying...")
                    await asyncio.sleep(self.config.db_retry_delay_s)
            raise Exception("Failed to create database connection pool after multiple attempts.")

    async def close(self):
        if self.pool:
            await self.pool.close()
    
    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS short_urls (
                    short_code VARCHAR(20) PRIMARY KEY,
                    url TEXT NOT NULL,
                    redirect_count INTEGER DEFAULT 0,
                    created TIMESTAMP DEFAULT NOW(),
                    updated TIMESTAMP DEFAULT NOW(),
                    last_accessed TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE
                );
            """)

    async def _insert_or_update_item(self, url, short_code, expires_at=None):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO short_urls (short_code, url, expires_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (short_code) DO UPDATE SET
                                url = EXCLUDED.url,
                                redirect_count = 0,
                                updated = NOW(),
                                expires_at = EXCLUDED.expires_at;
            """, short_code, url, expires_at)

    async def get_item(self, short_code):
        await self._remove_expired_items()
        async with self.pool.acquire() as conn:
            url = await conn.fetchrow("SELECT url FROM short_urls WHERE short_code = $1;", short_code)
            if url is None:
                return None
            url = url["url"]
            await conn.execute("UPDATE short_urls SET redirect_count = redirect_count + 1, last_accessed = NOW() WHERE short_code = $1;", short_code)
        return ShortURL(short_code, url)
    
    async def get_stats(self, short_code):
        print(f"Getting stats for short_code: {short_code}")
        await self._remove_expired_items()
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("SELECT redirect_count, created, updated, last_accessed FROM short_urls WHERE short_code = $1;", short_code)
            if stats is None:
                return None
            return {
                "redirect_count": stats["redirect_count"],
                "created": stats["created"],
                "updated": stats["updated"],
                "last_accessed": stats["last_accessed"]
            }
        
    async def search(self, url):
        await self._remove_expired_items()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT short_code FROM short_urls WHERE url = $1;", url)
            if not rows:
                return set()
            return {row["short_code"] for row in rows}
    
    async def _get_all_short_codes(self):
        await self._remove_expired_items()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT short_code FROM short_urls;")
            return {row["short_code"] for row in rows}    

    async def add_item(self, url, short_code=None, expires_at=None):
        if short_code is None:
            short_codes = await self._get_all_short_codes()
            while True:
                short_code = short_code_generator()
                if short_code not in short_codes:
                    break
        print(f"Adding item: {short_code} -> {url} with expires_at {expires_at}")
        await self._insert_or_update_item(url, short_code, expires_at)
        print(f"Added item: {short_code} -> {url} with expires_at {expires_at}")
        return short_code

    async def update_item(self, url, short_code, expires_at=None):
        print(f"Updating item: {short_code} -> {url} with expires_at {expires_at}")
        await self._remove_expired_items()
        await self._insert_or_update_item(url, short_code, expires_at)

    async def delete_item(self, short_code):
        print(f"Deleting item: {short_code}")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM short_urls WHERE short_code = $1;", short_code)

    async def _remove_expired_items(self):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM short_urls WHERE expires_at < NOW();")