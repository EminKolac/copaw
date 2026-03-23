"""SQLite database setup and CRUD operations for CoPaw recipes."""

import aiosqlite
import os
from pathlib import Path
from typing import Optional

def _resolve_db_path() -> Path:
    """Use /tmp on Vercel serverless, project root otherwise."""
    if os.environ.get("VERCEL"):
        return Path("/tmp/copaw.db")
    return Path(__file__).parent.parent / "copaw.db"


DB_PATH = _resolve_db_path()

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    image_local TEXT,
    category_id INTEGER REFERENCES categories(id),
    total_time TEXT,
    difficulty TEXT,
    servings INTEGER,
    source_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    amount TEXT,
    unit TEXT
);

CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id TEXT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    temperature TEXT,
    speed TEXT,
    duration TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingredients_recipe ON ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_steps_recipe ON steps(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category_id);
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()


# --- Categories ---

async def upsert_category(db: aiosqlite.Connection, name: str, slug: str) -> int:
    await db.execute(
        "INSERT OR IGNORE INTO categories (name, slug) VALUES (?, ?)",
        (name, slug),
    )
    cursor = await db.execute("SELECT id FROM categories WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    return row[0]


async def get_categories(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        "SELECT id, name, slug FROM categories ORDER BY name"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# --- Recipes ---

async def upsert_recipe(db: aiosqlite.Connection, recipe: dict) -> str:
    await db.execute(
        """INSERT OR REPLACE INTO recipes
           (id, title, description, image_url, image_local, category_id,
            total_time, difficulty, servings, source_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            recipe["id"],
            recipe["title"],
            recipe.get("description"),
            recipe.get("image_url"),
            recipe.get("image_local"),
            recipe.get("category_id"),
            recipe.get("total_time"),
            recipe.get("difficulty"),
            recipe.get("servings"),
            recipe.get("source_url"),
        ),
    )
    return recipe["id"]


async def upsert_ingredients(
    db: aiosqlite.Connection, recipe_id: str, ingredients: list[dict]
):
    await db.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    for ing in ingredients:
        await db.execute(
            """INSERT INTO ingredients (recipe_id, name, amount, unit)
               VALUES (?, ?, ?, ?)""",
            (recipe_id, ing["name"], ing.get("amount"), ing.get("unit")),
        )


async def upsert_steps(
    db: aiosqlite.Connection, recipe_id: str, steps: list[dict]
):
    await db.execute("DELETE FROM steps WHERE recipe_id = ?", (recipe_id,))
    for step in steps:
        await db.execute(
            """INSERT INTO steps (recipe_id, step_number, instruction,
               temperature, speed, duration) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                recipe_id,
                step["step_number"],
                step["instruction"],
                step.get("temperature"),
                step.get("speed"),
                step.get("duration"),
            ),
        )


async def get_recipes(
    db: aiosqlite.Connection,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where_clauses = []
    params: list = []

    if category_id:
        where_clauses.append("r.category_id = ?")
        params.append(category_id)
    if search:
        where_clauses.append("(r.title LIKE ? OR r.description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_cursor = await db.execute(
        f"SELECT COUNT(*) FROM recipes r {where}", params
    )
    total = (await count_cursor.fetchone())[0]

    cursor = await db.execute(
        f"""SELECT r.*, c.name as category_name, c.slug as category_slug
            FROM recipes r
            LEFT JOIN categories c ON r.category_id = c.id
            {where}
            ORDER BY r.scraped_at DESC
            LIMIT ? OFFSET ?""",
        params + [limit, offset],
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows], total


async def get_recipe_by_id(db: aiosqlite.Connection, recipe_id: str) -> Optional[dict]:
    cursor = await db.execute(
        """SELECT r.*, c.name as category_name, c.slug as category_slug
           FROM recipes r
           LEFT JOIN categories c ON r.category_id = c.id
           WHERE r.id = ?""",
        (recipe_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    recipe = dict(row)

    ing_cursor = await db.execute(
        "SELECT name, amount, unit FROM ingredients WHERE recipe_id = ? ORDER BY id",
        (recipe_id,),
    )
    recipe["ingredients"] = [dict(r) for r in await ing_cursor.fetchall()]

    steps_cursor = await db.execute(
        """SELECT step_number, instruction, temperature, speed, duration
           FROM steps WHERE recipe_id = ? ORDER BY step_number""",
        (recipe_id,),
    )
    recipe["steps"] = [dict(r) for r in await steps_cursor.fetchall()]

    return recipe


async def search_by_ingredients(
    db: aiosqlite.Connection, ingredient_names: list[str], min_match: int = 1
) -> list[dict]:
    """Find recipes matching at least min_match of the given ingredients."""
    placeholders = ",".join("?" for _ in ingredient_names)
    like_clauses = " OR ".join("i.name LIKE ?" for _ in ingredient_names)
    params = [f"%{name}%" for name in ingredient_names]

    cursor = await db.execute(
        f"""SELECT r.id, r.title, r.description, r.image_url, r.image_local,
                   r.total_time, r.difficulty, r.servings,
                   COUNT(DISTINCT i.name) as match_count,
                   GROUP_CONCAT(DISTINCT i.name) as matched_ingredients
            FROM recipes r
            JOIN ingredients i ON r.id = i.recipe_id
            WHERE {like_clauses}
            GROUP BY r.id
            HAVING match_count >= ?
            ORDER BY match_count DESC
            LIMIT 20""",
        params + [min_match],
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
