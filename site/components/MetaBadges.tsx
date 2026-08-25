import { DEVICES, type DeviceKey } from "../lib/devices";

const BADGE_CLASS =
  "rounded border border-neutral-200 bg-white px-2 py-0.5 text-xs text-neutral-600";

export function MetaBadges({
  ageRange,
  players,
  difficulty,
  devices,
}: {
  ageRange: string;
  players: string;
  difficulty: string;
  devices: DeviceKey[];
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <span className={BADGE_CLASS}>👶 {ageRange}</span>
      <span className={BADGE_CLASS}>🎮 {players}</span>
      <span className={BADGE_CLASS}>⭐ {difficulty}</span>
      {devices.map((device) => (
        <span key={device} className={BADGE_CLASS}>
          {DEVICES[device].icon} {DEVICES[device].label}
        </span>
      ))}
    </div>
  );
}
