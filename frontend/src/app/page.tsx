"use client";

import { useEffect, useState } from "react";
import { RecipeCard } from "@/components/RecipeCard";

interface Recipe {
  id: string;
  title: string;
  image_url: string;
  total_time: string;
  difficulty: string;
  category_name: string;
}

interface Category {
  id: number;
  name: string;
  slug: string;
}

export default function Home() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/recipes?limit=8").then((r) => r.json()),
      fetch("/api/categories").then((r) => r.json()),
    ])
      .then(([recipeData, catData]) => {
        setRecipes(recipeData.recipes || []);
        setCategories(catData.categories || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Hero */}
      <section className="mb-12 text-center">
        <h1 className="mb-4 text-5xl font-bold">
          <span className="gradient-text">CoPaw</span> ile Keşfet
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-[var(--text-secondary)]">
          Cookidoo tariflerini keşfet, elindeki malzemelerle ne pişirebileceğini
          yapay zeka ile öğren.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <a
            href="/recipes"
            className="rounded-lg border border-[var(--border)] px-6 py-3 font-medium hover:border-[var(--accent)] transition-colors"
          >
            Tarifleri Gör
          </a>
          <a
            href="/chat"
            className="rounded-lg bg-[var(--accent)] px-6 py-3 font-medium text-white hover:bg-[var(--accent-hover)] transition-colors"
          >
            🤖 Ne Pişirsem?
          </a>
        </div>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section className="mb-12">
          <h2 className="mb-4 text-2xl font-bold">Kategoriler</h2>
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <a
                key={cat.id}
                href={`/recipes?category=${cat.id}`}
                className="rounded-full border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--accent)] transition-colors"
              >
                {cat.name}
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Featured Recipes */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Son Eklenenler</h2>
          <a href="/recipes" className="text-[var(--accent)] hover:underline">
            Tümünü Gör →
          </a>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="h-72 animate-pulse rounded-xl bg-[var(--bg-secondary)]"
              />
            ))}
          </div>
        ) : recipes.length === 0 ? (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-12 text-center">
            <p className="text-4xl mb-4">🍳</p>
            <p className="text-[var(--text-secondary)]">
              Henüz tarif yok. Scraping başlatmak için backend API&apos;yi kullanın.
            </p>
            <code className="mt-2 block text-sm text-[var(--accent)]">
              POST /api/scrape {`{"max_recipes": 100}`}
            </code>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
