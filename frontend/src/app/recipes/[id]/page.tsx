"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

interface Ingredient {
  name: string;
  amount: string | null;
  unit: string | null;
}

interface Step {
  step_number: number;
  instruction: string;
  temperature: string | null;
  speed: string | null;
  duration: string | null;
}

interface Recipe {
  id: string;
  title: string;
  description: string;
  image_url: string;
  total_time: string;
  difficulty: string;
  servings: number;
  category_name: string;
  source_url: string;
  ingredients: Ingredient[];
  steps: Step[];
}

export default function RecipeDetailPage() {
  const params = useParams();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params?.id) return;
    fetch(`/api/recipes/${params.id}`)
      .then((r) => r.json())
      .then((data) => setRecipe(data.recipe))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [params?.id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <div className="h-80 animate-pulse rounded-xl bg-[var(--bg-secondary)]" />
        <div className="mt-6 h-8 w-2/3 animate-pulse rounded bg-[var(--bg-secondary)]" />
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center">
        <p className="text-4xl mb-4">😿</p>
        <p className="text-[var(--text-secondary)]">Tarif bulunamadı.</p>
        <a href="/recipes" className="mt-4 inline-block text-[var(--accent)] hover:underline">
          ← Tariflere Dön
        </a>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Back link */}
      <a href="/recipes" className="mb-4 inline-block text-sm text-[var(--text-secondary)] hover:text-[var(--accent)]">
        ← Tariflere Dön
      </a>

      {/* Hero image */}
      <div className="mb-6 overflow-hidden rounded-2xl">
        {recipe.image_url ? (
          <img
            src={recipe.image_url}
            alt={recipe.title}
            className="h-80 w-full object-cover"
          />
        ) : (
          <div className="flex h-80 items-center justify-center bg-[var(--bg-secondary)] text-6xl">
            🍽️
          </div>
        )}
      </div>

      {/* Title + Meta */}
      <h1 className="mb-4 text-3xl font-bold">{recipe.title}</h1>
      <div className="mb-6 flex flex-wrap gap-3">
        {recipe.total_time && (
          <span className="rounded-full bg-[var(--bg-secondary)] px-3 py-1 text-sm">
            ⏱️ {recipe.total_time}
          </span>
        )}
        {recipe.difficulty && (
          <span className="rounded-full bg-[var(--bg-secondary)] px-3 py-1 text-sm">
            📊 {recipe.difficulty}
          </span>
        )}
        {recipe.servings && (
          <span className="rounded-full bg-[var(--bg-secondary)] px-3 py-1 text-sm">
            🍽️ {recipe.servings} porsiyon
          </span>
        )}
        {recipe.category_name && (
          <span className="rounded-full bg-[var(--bg-secondary)] px-3 py-1 text-sm">
            📂 {recipe.category_name}
          </span>
        )}
      </div>

      {recipe.description && (
        <p className="mb-6 text-[var(--text-secondary)]">{recipe.description}</p>
      )}

      <div className="grid gap-8 md:grid-cols-2">
        {/* Ingredients */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <h2 className="mb-4 text-xl font-bold flex items-center gap-2">
            🥕 Malzemeler
          </h2>
          {recipe.ingredients.length === 0 ? (
            <p className="text-[var(--text-secondary)]">Malzeme bilgisi yok.</p>
          ) : (
            <ul className="space-y-2">
              {recipe.ingredients.map((ing, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 border-b border-[var(--border)] pb-2 last:border-0"
                >
                  <span className="mt-0.5 text-[var(--accent)]">•</span>
                  <span>
                    {ing.amount && (
                      <span className="font-medium text-[var(--accent-light)]">
                        {ing.amount} {ing.unit}{" "}
                      </span>
                    )}
                    {ing.name}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Steps */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-6">
          <h2 className="mb-4 text-xl font-bold flex items-center gap-2">
            👩‍🍳 Hazırlanışı
          </h2>
          {recipe.steps.length === 0 ? (
            <p className="text-[var(--text-secondary)]">
              Adım bilgisi mevcut değil.{" "}
              {recipe.source_url && (
                <a
                  href={recipe.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:underline"
                >
                  Cookidoo&apos;da görüntüle →
                </a>
              )}
            </p>
          ) : (
            <ol className="space-y-4">
              {recipe.steps.map((step) => (
                <li key={step.step_number} className="flex gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-bold text-white">
                    {step.step_number}
                  </span>
                  <div>
                    <p>{step.instruction}</p>
                    {(step.temperature || step.speed || step.duration) && (
                      <div className="mt-1 flex gap-2 text-xs text-[var(--text-secondary)]">
                        {step.temperature && <span>🌡️ {step.temperature}</span>}
                        {step.speed && <span>⚡ {step.speed}</span>}
                        {step.duration && <span>⏱️ {step.duration}</span>}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>

      {/* Cookidoo link */}
      {recipe.source_url && (
        <div className="mt-8 text-center">
          <a
            href={recipe.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-6 py-3 font-medium text-white hover:bg-[var(--accent-hover)] transition-colors"
          >
            Cookidoo&apos;da Aç ↗
          </a>
        </div>
      )}
    </div>
  );
}
