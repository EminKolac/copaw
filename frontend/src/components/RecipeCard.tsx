"use client";

interface Recipe {
  id: string;
  title: string;
  image_url: string;
  total_time: string;
  difficulty: string;
  category_name: string;
}

export function RecipeCard({ recipe }: { recipe: Recipe }) {
  const difficultyColor: Record<string, string> = {
    easy: "bg-green-500/20 text-green-400",
    medium: "bg-yellow-500/20 text-yellow-400",
    difficult: "bg-red-500/20 text-red-400",
  };

  return (
    <a href={`/recipes/${recipe.id}`} className="recipe-card block">
      <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--bg-card)]">
        <div className="relative h-48 bg-[var(--bg-secondary)]">
          {recipe.image_url ? (
            <img
              src={recipe.image_url}
              alt={recipe.title}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-4xl">
              🍽️
            </div>
          )}
          {recipe.difficulty && (
            <span
              className={`absolute right-2 top-2 rounded-full px-2 py-1 text-xs font-medium ${
                difficultyColor[recipe.difficulty.toLowerCase()] ||
                "bg-gray-500/20 text-gray-400"
              }`}
            >
              {recipe.difficulty}
            </span>
          )}
        </div>
        <div className="p-4">
          <h3 className="mb-2 line-clamp-2 font-semibold leading-tight">
            {recipe.title}
          </h3>
          <div className="flex items-center gap-3 text-xs text-[var(--text-secondary)]">
            {recipe.total_time && (
              <span className="flex items-center gap-1">
                ⏱️ {recipe.total_time}
              </span>
            )}
            {recipe.category_name && (
              <span className="flex items-center gap-1">
                📂 {recipe.category_name}
              </span>
            )}
          </div>
        </div>
      </div>
    </a>
  );
}
