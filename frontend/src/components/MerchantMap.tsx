import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import type { Merchant } from "../types";
import { TIER_COLORS, CATEGORY_LABELS, type Tier } from "../types";

interface MerchantMapProps {
  merchants: Merchant[];
  selectedId: string | null;
  onSelect: (merchant: Merchant) => void;
}

/* Fly to selected merchant */
function FlyToSelected({ merchant }: { merchant: Merchant | undefined }) {
  const map = useMap();
  const prevId = useRef<string | null>(null);

  useEffect(() => {
    if (merchant && merchant.place_id !== prevId.current) {
      map.flyTo([merchant.latitude, merchant.longitude], 15, {
        duration: 0.8,
      });
      prevId.current = merchant.place_id;
    }
  }, [merchant, map]);

  return null;
}

export default function MerchantMap({
  merchants,
  selectedId,
  onSelect,
}: MerchantMapProps) {
  const selected = merchants.find((m) => m.place_id === selectedId);

  return (
    <MapContainer
      center={[41.015, 28.98]}
      zoom={11}
      className="w-full h-full rounded-xl"
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FlyToSelected merchant={selected} />

      {merchants.map((m) => {
        const tier = (m.priority_tier ?? "LOW") as Tier;
        const color = TIER_COLORS[tier];
        const isSelected = m.place_id === selectedId;

        return (
          <CircleMarker
            key={m.place_id}
            center={[m.latitude, m.longitude]}
            radius={isSelected ? 10 : 6}
            pathOptions={{
              fillColor: color,
              fillOpacity: isSelected ? 1 : 0.7,
              color: isSelected ? "#ffffff" : color,
              weight: isSelected ? 3 : 1,
            }}
            eventHandlers={{
              click: () => onSelect(m),
            }}
          >
            <Popup>
              <div style={{ color: "#1e293b", minWidth: 160 }}>
                <strong style={{ fontSize: 14 }}>{m.name}</strong>
                <br />
                <span style={{ fontSize: 12, color: "#64748b" }}>
                  {CATEGORY_LABELS[m.category] ?? m.category} · {m.district}
                </span>
                <br />
                <span
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color,
                    marginTop: 4,
                    display: "inline-block",
                  }}
                >
                  Score: {m.moka_fit_score?.toFixed(1) ?? "N/A"}
                </span>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
