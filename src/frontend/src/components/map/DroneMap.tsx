import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Circle, Popup, Polyline, useMap } from 'react-leaflet';
import { createDroneIcon, createThreatIcon } from './MapMarker';
import type { DronePosition, MapThreatMarker } from '@/store/demoStore';
import { severityLabels } from '@/types';

interface DroneMapProps {
  drone: DronePosition | null;
  threats: MapThreatMarker[];
  trail?: Array<[number, number]>;
  className?: string;
}

const DEFAULT_CENTER: [number, number] = [39.9042, 116.4074];
const DEFAULT_ZOOM = 14;

function MapUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, map.getZoom(), { duration: 1 });
  }, [center[0], center[1], map]);
  return null;
}

export function DroneMap({ drone, threats, trail = [], className }: DroneMapProps) {
  const mapCenter: [number, number] = drone
    ? [drone.latitude, drone.longitude]
    : DEFAULT_CENTER;

  return (
    <MapContainer
      center={mapCenter}
      zoom={DEFAULT_ZOOM}
      className={className || 'w-full h-full rounded-lg'}
      zoomControl={true}
      attributionControl={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />

      {/* Auto-center on drone */}
      {drone && <MapUpdater center={[drone.latitude, drone.longitude]} />}

      {/* Drone marker */}
      {drone && (
        <>
          <Marker
            position={[drone.latitude, drone.longitude]}
            icon={createDroneIcon(drone.status)}
          >
            <Popup>
              <div className="text-xs space-y-1">
                <div className="font-bold text-sm">无人机</div>
                <div>高度: {drone.altitude.toFixed(1)}m</div>
                <div>速度: {drone.speed.toFixed(1)}m/s</div>
                <div>航向: {drone.heading.toFixed(0)}°</div>
                <div>状态: {drone.status === 'normal' ? '正常' : drone.status === 'warning' ? '警告' : '威胁'}</div>
              </div>
            </Popup>
          </Marker>

          {/* Signal range circle */}
          <Circle
            center={[drone.latitude, drone.longitude]}
            radius={500}
            pathOptions={{
              color: '#00E6A8',
              fillColor: '#00E6A8',
              fillOpacity: 0.05,
              weight: 1,
              dashArray: '5 5',
            }}
          />
        </>
      )}

      {/* Flight trail */}
      {trail.length > 1 && (
        <Polyline
          positions={trail}
          pathOptions={{
            color: '#00E6A8',
            weight: 2,
            opacity: 0.4,
            dashArray: '5 10',
          }}
        />
      )}

      {/* Threat markers */}
      {threats.map((threat) => (
        <Marker
          key={threat.threat_id}
          position={[threat.latitude, threat.longitude]}
          icon={createThreatIcon(threat.severity)}
        >
          <Popup>
            <div className="text-xs space-y-1">
              <div className="font-bold">{threat.threat_type}</div>
              <div>严重程度: {severityLabels[threat.severity]}</div>
              <div>{threat.description}</div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
