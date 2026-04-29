import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import type { DashboardPayload, EnergyAsset, RegionSentiment } from "../types";

type Layers = Record<string, boolean>;

export function EnergyMap({ data, layers }: { data: DashboardPayload; layers: Layers }) {
  const container = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

  useEffect(() => {
    if (!container.current || !token || mapRef.current) return;
    mapboxgl.accessToken = token;
    mapRef.current = new mapboxgl.Map({
      container: container.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [107, 31],
      zoom: 3.05,
      projection: "mercator"
    });
    mapRef.current.on("load", () => setMapReady(true));
  }, [token]);

  useEffect(() => {
    if (!mapReady || !mapRef.current) return;
    const map = mapRef.current;
    const regions = {
      type: "FeatureCollection",
      features: data.regionalSentiment.map((region) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: region.coordinates },
        properties: region
      }))
    } as GeoJSON.FeatureCollection;
    const assets = {
      type: "FeatureCollection",
      features: data.assets
        .filter((asset) => layerForAsset(asset, layers))
        .map((asset) => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: asset.coordinates },
          properties: asset
        }))
    } as GeoJSON.FeatureCollection;
    const demandSignals = {
      type: "FeatureCollection",
      features: (layers.demandSignals ? data.energyDemandSignals : []).map((signal) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: signal.coordinates },
        properties: signal
      }))
    } as GeoJSON.FeatureCollection;

    upsertSource(map, "regions", regions);
    upsertSource(map, "assets", assets);
    upsertSource(map, "demand-signals", demandSignals);
    if (!map.getLayer("region-heat")) {
      map.addLayer({
        id: "region-heat",
        type: "circle",
        source: "regions",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "demandIntensity"], 0, 12, 1, 44],
          "circle-color": ["case", ["<", ["get", "renewables"], 0], "#d94841", "#17a673"],
          "circle-opacity": 0.35,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#ffffff"
        }
      });
    }
    if (!map.getLayer("assets")) {
      map.addLayer({
        id: "assets",
        type: "circle",
        source: "assets",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "capacityGw"], 0, 5, 90, 18],
          "circle-color": ["match", ["get", "type"], "hydro", "#148f77", "nuclear", "#8b5cf6", "wind", "#3867d6", "oil_gas", "#c2410c", "#475569"],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#ffffff"
        }
      });
    }
    if (!map.getLayer("demand-signals")) {
      map.addLayer({
        id: "demand-signals",
        type: "circle",
        source: "demand-signals",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "demandScore"], 0, 7, 1, 18],
          "circle-color": "#f59e0b",
          "circle-opacity": 0.78,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#111827"
        }
      });
    }
  }, [data, layers, mapReady]);

  if (!token) {
    return <FallbackMap data={data} layers={layers} />;
  }

  return (
    <div className="relative h-[680px] overflow-hidden rounded-md border border-line bg-white shadow-sm">
      <div ref={container} className="h-full w-full" />
      <MapLegend />
    </div>
  );
}

function upsertSource(map: mapboxgl.Map, id: string, data: GeoJSON.FeatureCollection) {
  const existing = map.getSource(id) as mapboxgl.GeoJSONSource | undefined;
  if (existing) {
    existing.setData(data);
  } else {
    map.addSource(id, { type: "geojson", data });
  }
}

function layerForAsset(asset: EnergyAsset, layers: Layers) {
  if (asset.type === "wind") return layers.wind;
  if (asset.type === "hydro") return layers.hydro;
  if (asset.type === "nuclear") return layers.nuclear;
  if (asset.type === "oil_gas") return layers.oilGas;
  return true;
}

function FallbackMap({ data, layers }: { data: DashboardPayload; layers: Layers }) {
  return (
    <div className="relative h-[680px] overflow-hidden rounded-md border border-line bg-[#dfe7ee] shadow-sm">
      <div className="absolute inset-0 opacity-80" style={{ backgroundImage: "linear-gradient(#c8d2dd 1px, transparent 1px), linear-gradient(90deg, #c8d2dd 1px, transparent 1px)", backgroundSize: "56px 56px" }} />
      {data.regionalSentiment.map((region) => (
        <RegionBubble key={region.region} region={region} layers={layers} />
      ))}
      {data.assets.filter((asset) => layerForAsset(asset, layers)).map((asset) => (
        <AssetPoint key={asset.id} asset={asset} />
      ))}
      {layers.demandSignals && data.energyDemandSignals.map((signal) => (
        <DemandSignalPoint key={`${signal.region}-${signal.demandType}`} signal={signal} />
      ))}
      <div className="absolute left-5 top-5 rounded-md border border-line bg-white/90 p-4 shadow-sm">
        <p className="text-sm font-semibold">Global Energy Map</p>
        <p className="mt-1 max-w-[360px] text-xs leading-5 text-slate-600">Mapbox token not configured; using coordinate-projected fallback with sourced infrastructure and live-attempt dashboard layers.</p>
      </div>
      <MapLegend />
    </div>
  );
}

function RegionBubble({ region, layers }: { region: RegionSentiment; layers: Layers }) {
  const [x, y] = project(region.coordinates);
  const value = layers.supplyChain ? region.supplyChain : layers.chinaPolicy ? region.chinaPolicy : region.renewables;
  const color = value < -0.2 ? "#d94841" : value > 0.25 ? "#17a673" : "#f59e0b";
  return (
    <div className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/80 shadow-lg" style={{ left: `${x}%`, top: `${y}%`, width: `${34 + region.demandIntensity * 42}px`, height: `${34 + region.demandIntensity * 42}px`, background: color, opacity: 0.28 }} title={region.region} />
  );
}

function AssetPoint({ asset }: { asset: EnergyAsset }) {
  const [x, y] = project(asset.coordinates);
  const color = asset.type === "hydro" ? "#148f77" : asset.type === "nuclear" ? "#8b5cf6" : asset.type === "wind" ? "#3867d6" : "#c2410c";
  return (
    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${x}%`, top: `${y}%` }}>
      <div className="h-4 w-4 rounded-full border-2 border-white shadow" style={{ background: color }} />
      <div className="mt-1 whitespace-nowrap rounded bg-white/90 px-1.5 py-0.5 text-[10px] font-medium text-slate-700 shadow-sm">{asset.name}</div>
    </div>
  );
}

function DemandSignalPoint({ signal }: { signal: DashboardPayload["energyDemandSignals"][number] }) {
  const [x, y] = project(signal.coordinates);
  return (
    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${x}%`, top: `${y}%` }} title={`${signal.region}: ${signal.investmentRead}`}>
      <div className="grid h-6 w-6 place-items-center rounded-full border-2 border-ink bg-amber-400 text-[10px] font-bold text-ink shadow">
        {Math.round(signal.demandScore * 10)}
      </div>
      <div className="mt-1 max-w-[150px] rounded bg-white/95 px-1.5 py-0.5 text-[10px] font-medium leading-4 text-slate-700 shadow-sm">{signal.region}</div>
    </div>
  );
}

function project([lng, lat]: [number, number]) {
  return [((lng + 180) / 360) * 100, (1 - (lat + 60) / 145) * 100];
}

function MapLegend() {
  const items = [
    ["Hydro", "#148f77"],
    ["Wind", "#3867d6"],
    ["Nuclear", "#8b5cf6"],
    ["Oil & gas", "#c2410c"],
    ["Demand score", "#f59e0b"],
    ["Positive sentiment", "#17a673"],
    ["Negative sentiment", "#d94841"]
  ];
  return (
    <div className="absolute bottom-4 left-4 flex flex-wrap gap-2 rounded-md border border-line bg-white/90 p-3 text-xs shadow-sm">
      {items.map(([label, color]) => (
        <span key={label} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}
