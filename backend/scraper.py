"""Cookidoo scraper — fetches recipes from cookidoo.com.tr and stores them."""

import asyncio
import logging
import os
import re
from pathlib import Path

import aiohttp
from cookidoo_api import Cookidoo
from cookidoo_api.types import (
    CookidooConfig,
    CookidooLocalizationConfig,
    CookidooShoppingRecipeDetails,
)
from dotenv import load_dotenv

from database import get_db, init_db, upsert_category, upsert_ingredients, upsert_recipe, upsert_steps

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

TR_CONFIG = CookidooConfig(
    localization=CookidooLocalizationConfig(
        country_code="tr",
        language="tr-TR",
        url="https://cookidoo.com.tr/foundation/tr-TR",
    ),
    email=os.getenv("COOKIDOO_EMAIL", ""),
    password=os.getenv("COOKIDOO_PASSWORD", ""),
)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


async def download_image(session: aiohttp.ClientSession, url: str, recipe_id: str) -> str | None:
    """Download recipe image and return local path."""
    if not url:
        return None
    try:
        ext = ".jpg"
        local_path = IMAGES_DIR / f"{recipe_id}{ext}"
        if local_path.exists():
            return str(local_path.relative_to(Path(__file__).parent.parent))

        async with session.get(url) as resp:
            if resp.status == 200:
                content = await resp.read()
                local_path.write_bytes(content)
                return str(local_path.relative_to(Path(__file__).parent.parent))
    except Exception as e:
        log.warning(f"Failed to download image for {recipe_id}: {e}")
    return None


async def parse_recipe_details(details: CookidooShoppingRecipeDetails) -> dict:
    """Convert cookidoo-api type to our DB-friendly dict."""
    # Parse ingredients
    ingredients = []
    for ing in details.ingredients:
        # The description often contains "amount unit name" format
        desc = ing.description.strip() if ing.description else ""
        name = ing.name.strip() if ing.name else desc

        # Try to parse amount/unit from description
        amount = None
        unit = None
        if desc:
            parts = desc.split(" ", 2)
            if len(parts) >= 2 and parts[0].replace(",", "").replace(".", "").isdigit():
                amount = parts[0]
                if len(parts) >= 3:
                    unit = parts[1]
                    if not name:
                        name = parts[2]
                elif not name:
                    name = parts[1]

        if name:
            ingredients.append({"name": name, "amount": amount, "unit": unit})

    # Parse categories
    categories = []
    for cat in details.categories:
        categories.append({"id": cat.id, "name": cat.name})

    # Notes as steps (cookidoo doesn't expose step-by-step via this API)
    steps = []
    for i, note in enumerate(details.notes, 1):
        steps.append({
            "step_number": i,
            "instruction": note,
            "temperature": None,
            "speed": None,
            "duration": None,
        })

    return {
        "id": details.id,
        "title": details.name,
        "description": "",
        "difficulty": details.difficulty,
        "servings": _parse_servings(details.serving_size),
        "total_time": f"{details.total_time} min" if details.total_time else None,
        "active_time": details.active_time,
        "ingredients": ingredients,
        "steps": steps,
        "categories": categories,
        "utensils": details.utensils,
        "collections": [{"id": c.id, "name": c.name} for c in details.collections],
    }


def _parse_servings(serving_size: str) -> int | None:
    if not serving_size:
        return None
    match = re.search(r"\d+", serving_size)
    return int(match.group()) if match else None


async def scrape_all(max_recipes: int = 500):
    """Main scraping flow: login → get collections → get recipes → store."""
    log.info("Initializing database...")
    await init_db()

    async with aiohttp.ClientSession() as session:
        cookidoo = Cookidoo(session, TR_CONFIG)

        log.info("Logging in to Cookidoo...")
        try:
            await cookidoo.login()
        except Exception as e:
            log.error(f"Login failed: {e}")
            return

        log.info("Login successful!")
        sub = await cookidoo.get_active_subscription()
        if sub:
            log.info(f"Subscription: {sub.status}, expires: {sub.expires}")

        # Collect recipe IDs from managed collections
        recipe_ids: set[str] = set()

        log.info("Fetching managed collections...")
        page = 0
        while True:
            try:
                collections = await cookidoo.get_managed_collections(page=page)
                if not collections:
                    break
                for col in collections:
                    log.info(f"  Collection: {col.name} ({len(col.chapters)} chapters)")
                    for chapter in col.chapters:
                        for recipe in chapter.recipes:
                            recipe_ids.add(recipe.id)
                page += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                log.warning(f"Error fetching collections page {page}: {e}")
                break

        log.info(f"Fetching custom collections...")
        page = 0
        while True:
            try:
                collections = await cookidoo.get_custom_collections(page=page)
                if not collections:
                    break
                for col in collections:
                    log.info(f"  Custom collection: {col.name}")
                    for chapter in col.chapters:
                        for recipe in chapter.recipes:
                            recipe_ids.add(recipe.id)
                page += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                log.warning(f"Error fetching custom collections page {page}: {e}")
                break

        log.info(f"Found {len(recipe_ids)} unique recipe IDs")

        if len(recipe_ids) > max_recipes:
            recipe_ids = set(list(recipe_ids)[:max_recipes])
            log.info(f"Limiting to {max_recipes} recipes")

        # Fetch recipe details and store
        db = await get_db()
        try:
            fetched = 0
            failed = 0
            for rid in recipe_ids:
                try:
                    details = await cookidoo.get_recipe_details(rid)
                    parsed = await parse_recipe_details(details)

                    # Handle categories
                    cat_id = None
                    if parsed["categories"]:
                        first_cat = parsed["categories"][0]
                        cat_id = await upsert_category(
                            db, first_cat["name"], slugify(first_cat["name"])
                        )

                    # Build image URL from cookidoo
                    image_url = f"https://assets.tmecosys.com/image/upload/t_web_recipe_detail/img/recipe/{rid}"
                    image_local = await download_image(session, image_url, rid)

                    # Store recipe
                    await upsert_recipe(db, {
                        "id": parsed["id"],
                        "title": parsed["title"],
                        "description": parsed["description"],
                        "image_url": image_url,
                        "image_local": image_local,
                        "category_id": cat_id,
                        "total_time": parsed["total_time"],
                        "difficulty": parsed["difficulty"],
                        "servings": parsed["servings"],
                        "source_url": f"https://cookidoo.com.tr/recipes/recipe/tr-TR/{rid}",
                    })

                    # Store ingredients and steps
                    await upsert_ingredients(db, parsed["id"], parsed["ingredients"])
                    if parsed["steps"]:
                        await upsert_steps(db, parsed["id"], parsed["steps"])

                    await db.commit()
                    fetched += 1

                    if fetched % 10 == 0:
                        log.info(f"Progress: {fetched}/{len(recipe_ids)} recipes")

                    await asyncio.sleep(1)  # Rate limiting

                except Exception as e:
                    log.warning(f"Failed to fetch recipe {rid}: {e}")
                    failed += 1

            log.info(f"Done! Fetched: {fetched}, Failed: {failed}")
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(scrape_all())
