"""CoPaw FastAPI backend — recipe browsing + AI chat."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import (
    get_db,
    get_categories,
    get_recipe_by_id,
    get_recipes,
    init_db,
    search_by_ingredients,
)
from chat import chat_with_ingredients


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="CoPaw", description="AI Recipe Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static images
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# --- Models ---

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    matched_recipes: list[dict]


class RecipeListResponse(BaseModel):
    recipes: list[dict]
    total: int
    page: int
    limit: int


class ScrapeRequest(BaseModel):
    max_recipes: int = 500


# --- Endpoints ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "copaw"}


@app.get("/api/categories")
async def list_categories():
    db = await get_db()
    try:
        categories = await get_categories(db)
        return {"categories": categories}
    finally:
        await db.close()


@app.get("/api/recipes", response_model=RecipeListResponse)
async def list_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
):
    db = await get_db()
    try:
        offset = (page - 1) * limit
        recipes, total = await get_recipes(db, category_id, search, limit, offset)
        return RecipeListResponse(recipes=recipes, total=total, page=page, limit=limit)
    finally:
        await db.close()


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    db = await get_db()
    try:
        recipe = await get_recipe_by_id(db, recipe_id)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"recipe": recipe}
    finally:
        await db.close()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Extract ingredient names from the message (simple split)
    ingredients = [
        i.strip().lower()
        for i in req.message.replace(",", " ").replace("ve ", " ").split()
        if len(i.strip()) > 2
    ]

    # Search DB for matching recipes
    db = await get_db()
    try:
        matched = await search_by_ingredients(db, ingredients, min_match=1)
    finally:
        await db.close()

    # Get AI response
    reply = await chat_with_ingredients(req.message, matched)

    return ChatResponse(reply=reply, matched_recipes=matched[:10])


@app.post("/api/scrape")
async def trigger_scrape(req: ScrapeRequest):
    """Trigger recipe scraping in background."""
    from scraper import scrape_all

    asyncio.create_task(scrape_all(req.max_recipes))
    return {"status": "scraping_started", "max_recipes": req.max_recipes}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
