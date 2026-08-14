export function MetaBadges({
  ageRange,
  players,
  difficulty,
}: {
  ageRange: string;
  players: string;
  difficulty: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        👶 {ageRange}
      </span>
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        🎮 {players}
      </span>
      <span className="rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600">
        ⭐ {difficulty}
      </span>
    </div>
  );
}
