"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
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

export default function RecipesPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-7xl px-4 py-8">Yükleniyor...</div>}>
      <RecipesContent />
    </Suspense>
  );
}

function RecipesContent() {
  const searchParams = useSearchParams();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<number | null>(
    searchParams?.get("category") ? Number(searchParams.get("category")) : null
  );

  const limit = 20;

  const fetchRecipes = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (selectedCategory) params.set("category_id", selectedCategory.toString());
    if (search) params.set("search", search);

    try {
      const res = await fetch(`/api/recipes?${params}`);
      const data = await res.json();
      setRecipes(data.recipes || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, selectedCategory, search]);

  useEffect(() => {
    fetch("/api/categories")
      .then((r) => r.json())
      .then((data) => setCategories(data.categories || []))
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetchRecipes();
  }, [fetchRecipes]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">Tarifler</h1>

      {/* Search + Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Tarif ara..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-4 py-3 pl-10 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-[var(--accent)] focus:outline-none"
          />
          <span className="absolute left-3 top-3.5 text-[var(--text-secondary)]">
            🔍
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => {
              setSelectedCategory(null);
              setPage(1);
            }}
            className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
              !selectedCategory
                ? "bg-[var(--accent)] text-white"
                : "border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]"
            }`}
          >
            Tümü
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => {
                setSelectedCategory(cat.id);
                setPage(1);
              }}
              className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                selectedCategory === cat.id
                  ? "bg-[var(--accent)] text-white"
                  : "border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)]"
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p className="mb-4 text-sm text-[var(--text-secondary)]">
        {total} tarif bulundu
      </p>

      {/* Recipe Grid */}
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
          <p className="text-4xl mb-4">🔍</p>
          <p className="text-[var(--text-secondary)]">
            Aramanızla eşleşen tarif bulunamadı.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {recipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm disabled:opacity-50 hover:border-[var(--accent)] transition-colors"
          >
            ← Önceki
          </button>
          <span className="px-4 text-sm text-[var(--text-secondary)]">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm disabled:opacity-50 hover:border-[var(--accent)] transition-colors"
          >
            Sonraki →
          </button>
        </div>
      )}
    </div>
  );
}
