import L from 'leaflet';

// Drone marker icon (SVG-based)
export function createDroneIcon(status: 'normal' | 'warning' | 'threat' = 'normal') {
  const colorMap = {
    normal: '#00E6A8',
    warning: '#fbbf24',
    threat: '#f43f5e',
  };
  const color = colorMap[status];

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="14" fill="${color}20" stroke="${color}" stroke-width="1.5"/>
      <circle cx="18" cy="18" r="6" fill="${color}40" stroke="${color}" stroke-width="1"/>
      <circle cx="18" cy="18" r="2" fill="${color}"/>
      <line x1="6" y1="6" x2="14" y2="14" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="30" y1="6" x2="22" y2="14" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="6" y1="30" x2="14" y2="22" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="30" y1="30" x2="22" y2="22" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  `;

  return L.divIcon({
    html: svg,
    className: 'drone-marker',
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

// Threat marker icon
export function createThreatIcon(severity: 'low' | 'medium' | 'high' | 'critical' = 'medium') {
  const colorMap = {
    low: '#00E6A8',
    medium: '#fbbf24',
    high: '#f59e0b',
    critical: '#f43f5e',
  };
  const color = colorMap[severity];
  const size = severity === 'critical' ? 10 : severity === 'high' ? 8 : 6;

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size * 2 + 4}" height="${size * 2 + 4}" viewBox="0 0 ${size * 2 + 4} ${size * 2 + 4}">
      <circle cx="${size + 2}" cy="${size + 2}" r="${size}" fill="${color}60" stroke="${color}" stroke-width="1.5"/>
      <circle cx="${size + 2}" cy="${size + 2}" r="2" fill="${color}"/>
    </svg>
  `;

  return L.divIcon({
    html: svg,
    className: 'threat-marker',
    iconSize: [size * 2 + 4, size * 2 + 4],
    iconAnchor: [size + 2, size + 2],
  });
}
