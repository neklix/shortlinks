from fastapi import  FastAPI, HTTPException
from datetime import datetime
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
import uvicorn
from config import Config
from storage import Database
from urllib.parse import unquote
from typing import Optional


config = Config()
app = FastAPI()
db = Database(config)

class ShortUrlModelRequest(BaseModel):
    """
    Request model for creating a short URL.

    Attributes:
        url (str): The original URL to be shortened.
        custom_alias (str, optional): A custom alias for the short URL.
        expires_at (datetime, optional): Expiration date for the short URL.
    """
    url: str
    custom_alias: str = None
    expires_at: Optional[datetime] = None

class ShortUrlModelUpdateRequest(BaseModel):
    """
    Request model for updating a short URL.

    Attributes:
        url (str): The updated original URL.
        expires_at (datetime, optional): Updated expiration date for the short URL.
    """
    url: str
    expires_at: Optional[datetime] = None

class ShortUrlModelResponse(BaseModel):
    """
    Response model for short URL operations.

    Attributes:
        url (str): The original URL.
        short_code (str, optional): The generated or custom short code.
        expires_at (datetime, optional): Expiration date for the short URL.
    """
    url: str
    short_code: str = None
    expires_at: Optional[datetime] = None

class ShortUrlModelStatsResponse(BaseModel):
    """
    Response model for short URL statistics.

    Attributes:
        redirect_count (int): Number of times the short URL has been accessed.
        created (datetime): Creation timestamp of the short URL.
        updated (datetime): Last update timestamp of the short URL.
        last_accessed (datetime): Last access timestamp of the short URL.
    """
    redirect_count: int
    created: datetime
    updated: datetime
    last_accessed: datetime

class ShortUrlListResponse(BaseModel):
    """
    Response model for listing short codes.

    Attributes:
        short_codes (list[str]): List of short codes matching the search criteria.
    """
    short_codes: list[str]


@app.on_event("startup")
async def startup_event():
    """
    Event handler for application startup.
    Initializes the database connection.
    """
    await db.init_db()

@app.get("/links/search", response_model=ShortUrlListResponse)
async def search_url(url: str):
    """
    Search for short codes associated with a given URL.

    Args:
        url (str): The URL to search for.

    Returns:
        ShortUrlListResponse: A list of matching short codes.

    Raises:
        HTTPException: If no short codes are found for the given URL.
    """
    url = unquote(url)
    print(f"Searching for URL: {url}")
    short_codes = await db.search(url)
    if not short_codes:
        raise HTTPException(status_code=404, detail="ShortUrl not found")
    return {"short_codes": list(short_codes)}

@app.get("/links/{short_code}")
async def redirect(short_code: str):
    """
    Redirect to the original URL associated with a short code.

    Args:
        short_code (str): The short code to resolve.

    Returns:
        RedirectResponse: A redirect response to the original URL.

    Raises:
        HTTPException: If the short code is not found.
    """
    url = await db.get_item(short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="ShortUrl not found!")
    return RedirectResponse(url.url)

@app.post("/links/shorten", response_model=ShortUrlModelResponse)
async def create_url(request: ShortUrlModelRequest):
    """
    Create a new short URL.

    Args:
        request (ShortUrlModelRequest): The request data for creating a short URL.

    Returns:
        ShortUrlModelResponse: The created short URL details.

    Raises:
        HTTPException: If the short URL already exists.
    """
    short_code = await db.add_item(request.url, request.custom_alias, request.expires_at)
    if short_code is None:
        raise HTTPException(status_code=400, detail="ShortUrl already exists")
    return {"short_code": short_code, "url": request.url, "expires_at": request.expires_at}

@app.delete("/links/{short_code}", response_model=ShortUrlModelResponse)
async def delete_url(short_code: str):
    """
    Delete a short URL.

    Args:
        short_code (str): The short code to delete.

    Returns:
        ShortUrlModelResponse: The details of the deleted short URL.

    Raises:
        HTTPException: If the short code is not found.
    """
    url = await db.get_item(short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="ShortUrl not found")
    await db.delete_item(short_code)
    return {"short_code": short_code, "url": url.url}

@app.put("/links/{short_code}", response_model=ShortUrlModelResponse)
async def update_url(short_code: str, request: ShortUrlModelUpdateRequest):
    """
    Update an existing short URL.

    Args:
        short_code (str): The short code to update.
        request (ShortUrlModelUpdateRequest): The updated data for the short URL.

    Returns:
        ShortUrlModelResponse: The updated short URL details.

    Raises:
        HTTPException: If the short code is not found.
    """
    url = await db.get_item(short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="ShortUrl not found")
    await db.update_item(request.url, short_code, request.expires_at)
    return {"short_code": short_code, "url": request.url, "expires_at": request.expires_at}

@app.get("/links/{short_code}/stats", response_model=ShortUrlModelStatsResponse)
async def get_stats(short_code: str):
    """
    Retrieve statistics for a short URL.

    Args:
        short_code (str): The short code to retrieve statistics for.

    Returns:
        ShortUrlModelStatsResponse: The statistics of the short URL.

    Raises:
        HTTPException: If the short code is not found.
    """
    url = await db.get_item(short_code)
    if url is None:
        raise HTTPException(status_code=404, detail="ShortUrl not found")
    stats = await db.get_stats(short_code)
    return {
        "redirect_count": stats["redirect_count"],
        "created": stats["created"],
        "updated": stats["updated"],
        "last_accessed": stats["last_accessed"],
    }

@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler for application shutdown.
    Closes the database connection.
    """
    await db.close()

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, workers=2)
