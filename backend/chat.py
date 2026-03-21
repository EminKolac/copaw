"""Gemini-powered chat for ingredient-based recipe suggestions."""

import os
import json
import logging
import aiohttp
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

SYSTEM_PROMPT = """Sen CoPaw, Türk mutfağı konusunda uzman bir yapay zeka yemek asistanısın.
Cookidoo veritabanından tarif önerileri yapıyorsun.

Görevin:
1. Kullanıcının elindeki malzemelere göre yapabileceği yemekleri öner
2. Veritabanından eşleşen tarifleri kullan ve tarif ID'leriyle birlikte sun
3. Eksik malzemeler için alternatif öneriler yap
4. Tarifin zorluk derecesini ve süresini belirt
5. Kullanıcı hangi dilde yazarsa o dilde yanıt ver (Türkçe veya İngilizce)

Yanıt formatı:
- Her tarif için: isim, eşleşen malzemeler, eksik malzemeler, süre, zorluk
- Pratik pişirme ipuçları ekle
- Samimi ve yardımsever ol

Eğer veritabanında eşleşen tarif yoksa, genel yemek önerileri yap ama bunu belirt."""


def _build_fallback_response(matched_recipes: list[dict], user_message: str) -> str:
    """Generate a simple response without LLM when Gemini is unavailable."""
    if not matched_recipes:
        return (
            "Veritabanında eşleşen tarif bulunamadı. "
            "Daha fazla malzeme eklemeyi veya farklı malzemeler denemeyi düşünebilirsin!"
        )

    lines = ["Elindeki malzemelere göre şu tarifleri buldum:\n"]
    for r in matched_recipes[:5]:
        lines.append(
            f"**{r['title']}** — {r.get('match_count', '?')} malzeme eşleşti "
            f"({r.get('matched_ingredients', '')}), "
            f"Süre: {r.get('total_time', '?')}, "
            f"Zorluk: {r.get('difficulty', '?')}"
        )
    lines.append("\nDetaylar için tarife tıklayabilirsin!")
    return "\n".join(lines)


async def chat_with_ingredients(
    user_message: str,
    matched_recipes: list[dict],
) -> str:
    """Send user ingredients + matched recipes to Gemini for meal suggestions."""

    # Build context from matched recipes
    recipe_context = ""
    if matched_recipes:
        recipe_context = "\n\nVERİTABANINDAKİ EŞLEŞEN TARİFLER:\n"
        for r in matched_recipes:
            recipe_context += f"""
---
Tarif ID: {r['id']}
İsim: {r['title']}
Eşleşen Malzeme Sayısı: {r.get('match_count', '?')}
Eşleşen Malzemeler: {r.get('matched_ingredients', '?')}
Süre: {r.get('total_time', 'Belirtilmemiş')}
Zorluk: {r.get('difficulty', 'Belirtilmemiş')}
Porsiyon: {r.get('servings', 'Belirtilmemiş')}
"""
    else:
        recipe_context = "\n\nVeritabanında eşleşen tarif bulunamadı. Genel öneriler yap."

    full_prompt = f"{SYSTEM_PROMPT}\n{recipe_context}\n\nKULLANICI: {user_message}"

    # Try Gemini API via REST (more reliable than SDK in some environments)
    try:
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GEMINI_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text
                else:
                    log.warning(f"Gemini API returned {resp.status}")
                    return _build_fallback_response(matched_recipes, user_message)
    except Exception as e:
        log.warning(f"Gemini API error: {e}")
        return _build_fallback_response(matched_recipes, user_message)
