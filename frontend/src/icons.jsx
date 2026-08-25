const base = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export const GraduationCapIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M22 10 12 5 2 10l10 5 10-5Z" />
    <path d="M6 12v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5" />
  </svg>
);

export const FormIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="4" y="3" width="16" height="18" rx="2" />
    <path d="M8 8h8M8 12h8M8 16h5" />
  </svg>
);

export const ChartIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M3 3v18h18" />
    <rect x="7" y="12" width="3" height="6" />
    <rect x="12.5" y="8" width="3" height="10" />
    <rect x="18" y="5" width="3" height="13" />
  </svg>
);

export const UserIcon = (props) => (
  <svg {...base} {...props}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
  </svg>
);

export const FlaskIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M9 3h6M10 3v6l-5.5 9a2 2 0 0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 9V3" />
  </svg>
);

export const ScissorsIcon = (props) => (
  <svg {...base} {...props}>
    <circle cx="6" cy="6" r="3" />
    <circle cx="6" cy="18" r="3" />
    <path d="M8.5 8.5 20 20M20 4 8.5 15.5" />
  </svg>
);

export const ListIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M9 6h11M9 12h11M9 18h11" />
    <circle cx="4.5" cy="6" r="1" fill="currentColor" stroke="none" />
    <circle cx="4.5" cy="12" r="1" fill="currentColor" stroke="none" />
    <circle cx="4.5" cy="18" r="1" fill="currentColor" stroke="none" />
  </svg>
);

export const CheckCircleIcon = (props) => (
  <svg {...base} {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8.5 12.5 2.3 2.3L16 10" />
  </svg>
);

export const AlertTriangleIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 3 2 20h20L12 3Z" />
    <path d="M12 9.5v5M12 17h.01" />
  </svg>
);

export const AlertCircleIcon = (props) => (
  <svg {...base} {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16h.01" />
  </svg>
);

export const HistoryIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M3 12a9 9 0 1 0 3-6.7" />
    <path d="M3 4v5h5" />
    <path d="M12 8v5l3 2" />
  </svg>
);

export const DatabaseIcon = (props) => (
  <svg {...base} {...props}>
    <ellipse cx="12" cy="5" rx="8" ry="3" />
    <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
    <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
  </svg>
);

export const GridIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
  </svg>
);

export const ScaleIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 3v18M7 21h10" />
    <path d="M5 7h6M13 7h6" />
    <path d="M5 7 2 13a3 3 0 0 0 6 0L5 7ZM19 7l-3 6a3 3 0 0 0 6 0l-3-6Z" />
  </svg>
);

export const ImageIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <circle cx="9" cy="9" r="2" />
    <path d="m21 15-5-5L5 21" />
  </svg>
);

export const ArrowUpIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 19V5M5 12l7-7 7 7" />
  </svg>
);

export const ArrowDownIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M12 5v14M19 12l-7 7-7-7" />
  </svg>
);
