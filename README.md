# CoPaw - AI Recipe Assistant

CoPaw is a Cookidoo recipe scraper and AI-powered recipe assistant for Turkish cuisine. Browse recipes, search by ingredients, and get AI-powered meal suggestions.

## Features

- **Recipe Scraping** — Automatically fetch recipes from your Cookidoo (cookidoo.com.tr) account
- **Recipe Browser** — Browse, search, and filter recipes by category
- **AI Chat** — Tell CoPaw what ingredients you have, and it suggests what to cook (powered by Gemini)
- **Recipe Details** — Full ingredient lists, step-by-step instructions, and Cookidoo links
- **Demo Mode** — Comes with 12 sample Turkish recipes to try without a Cookidoo account

## Tech Stack

| Layer    | Technology                         |
|----------|------------------------------------|
| Backend  | Python 3.11+, FastAPI, aiosqlite  |
| Frontend | Next.js 16, React 19, Tailwind 4  |
| AI       | Google Gemini 2.0 Flash           |
| Scraper  | cookidoo-api                       |
| Database | SQLite (file-based, zero config)   |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Clone the repo

```bash
git clone https://github.com/EminKolac/copaw.git
cd copaw
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env with your credentials (see Configuration below)

# Seed demo data (works without Cookidoo account)
python seed_data.py

# Start the API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend setup (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the app

Visit **http://localhost:3000**

## Configuration

Edit `backend/.env`:

```env
# Required only for scraping real recipes from Cookidoo
COOKIDOO_EMAIL=your_email@example.com
COOKIDOO_PASSWORD=your_password

# Optional — enables AI chat (free at https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_api_key
```

**Without any credentials**, you can still:
- Browse the 12 demo recipes (run `python seed_data.py` first)
- Search and filter recipes
- View recipe details

**With Gemini API key**, you additionally get:
- AI-powered ingredient-based recipe suggestions

**With Cookidoo credentials**, you additionally get:
- Scraping hundreds of real recipes from your Cookidoo subscription

## Scraping Recipes

Once you have Cookidoo credentials in `.env`:

```bash
# Option 1: Run the scraper directly
cd backend
python scraper.py

# Option 2: Trigger via API (scrapes in background)
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"max_recipes": 100}'
```

## API Endpoints

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| GET    | `/api/health`         | Health check                   |
| GET    | `/api/categories`     | List all categories            |
| GET    | `/api/recipes`        | List recipes (paginated)       |
| GET    | `/api/recipes/:id`    | Get recipe details             |
| POST   | `/api/chat`           | AI chat with ingredients       |
| POST   | `/api/scrape`         | Trigger background scraping    |

### Query Parameters for `/api/recipes`

- `page` — Page number (default: 1)
- `limit` — Items per page (default: 20, max: 100)
- `category_id` — Filter by category
- `search` — Search by recipe title

## Project Structure

```
copaw/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── database.py       # SQLite schema & CRUD
│   ├── scraper.py        # Cookidoo scraper
│   ├── chat.py           # Gemini AI chat
│   ├── seed_data.py      # Demo data seeder
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Home page
│   │   │   ├── recipes/page.tsx  # Recipe browser
│   │   │   ├── recipes/[id]/     # Recipe detail
│   │   │   └── chat/page.tsx     # AI chat
│   │   └── components/
│   │       └── RecipeCard.tsx
│   ├── next.config.ts    # API proxy to backend
│   └── package.json
├── static/images/        # Downloaded recipe images
└── copaw.db              # SQLite database (auto-created)
```

## License

MIT
