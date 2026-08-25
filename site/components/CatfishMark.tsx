export function CatfishMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true" focusable="false">
      <g fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round">
        <path d="M23 45 Q16 55 9 55" />
        <path d="M41 45 Q48 55 55 55" />
      </g>
      <path
        d="M37 28.5 C45.2 25.2 48.1 22.6 50.5 17 L51.8 19.2 C52.4 24.8 49.9 28.7 45.5 33 Z"
        fill="currentColor"
      />
      <ellipse
        cx="53.3"
        cy="13"
        rx="7"
        ry="4.6"
        transform="rotate(-66.8 53.3 13)"
        fill="currentColor"
      />
      <path d="M15 39 C 8 40 4 46 5 53 C 11 51 16 47 19 43 Z" fill="currentColor" />
      <path d="M49 39 C 56 40 60 46 59 53 C 53 51 48 47 45 43 Z" fill="currentColor" />
      <ellipse cx="32" cy="34" rx="20" ry="14" fill="currentColor" />
      <path
        d="M23.5 40.5 Q32 37 40.5 40.5"
        fill="none"
        stroke="#fff"
        strokeWidth="2.8"
        strokeLinecap="round"
      />
      <circle cx="24" cy="29" r="3.4" fill="#fff" />
      <circle cx="40" cy="29" r="3.4" fill="#fff" />
      <circle cx="24" cy="29" r="1.7" fill="currentColor" />
      <circle cx="40" cy="29" r="1.7" fill="currentColor" />
    </svg>
  );
}
