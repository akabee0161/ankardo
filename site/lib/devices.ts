export type DeviceKey = "pc" | "mobile-landscape" | "mobile-portrait";

export type DeviceInfo = {
  label: string;
  icon: string;
};

export const DEVICES: Record<DeviceKey, DeviceInfo> = {
  pc: { label: "PC", icon: "💻" },
  "mobile-landscape": { label: "スマホ・タブレット（横向き）", icon: "📱" },
  "mobile-portrait": { label: "スマホ・タブレット（縦向き）", icon: "📱" },
};
