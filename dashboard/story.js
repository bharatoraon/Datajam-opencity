import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// Initialize map
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  center: [77.5946, 12.9716],
  zoom: 10.5,
  pitch: 45,
  bearing: -17.6,
  interactive: false // Disable map interactions so scroll only controls story
});

const chapters = {
  'chapter-1': {
    bearing: -17.6,
    center: [77.5946, 12.9716],
    zoom: 11,
    pitch: 45,
    layers: ['layer-raw-water']
  },
  'chapter-2': {
    bearing: 0,
    center: [77.5835778, 12.9604137], // Specific risk point
    zoom: 14,
    pitch: 60,
    layers: ['layer-raw-water', 'layer-raw-sewage', 'layer-raw-manholes', 'layer-risk-heatmap']
  },
  'chapter-3': {
    bearing: 45,
    center: [77.6698, 12.9360], // Bellandur Lake area
    zoom: 13,
    pitch: 40,
    layers: ['layer-primary-drains', 'layer-secondary-drains', 'layer-lakes-existing', 'layer-lakes-lost']
  },
  'chapter-4': {
    bearing: 0,
    center: [77.5946, 12.9716],
    zoom: 10.5,
    pitch: 0,
    layers: ['layer-ward-risk', 'layer-slums']
  },
  'chapter-5': {
    bearing: -20,
    center: [77.625390, 13.067339], // A specific audit point
    zoom: 15,
    pitch: 60,
    layers: ['layer-audits']
  }
};

const allLayers = [
  'layer-raw-water', 'layer-raw-sewage', 'layer-raw-manholes', 'layer-risk-heatmap',
  'layer-primary-drains', 'layer-secondary-drains', 'layer-lakes-existing', 'layer-lakes-lost',
  'layer-ward-risk', 'layer-slums', 'layer-audits'
];

map.on('load', () => {
  // Load ALL sources and layers first
  map.addSource('raw-water', { type: 'geojson', data: './Moddata/raw_water.geojson' });
  map.addSource('raw-sewage', { type: 'geojson', data: './Moddata/raw_sewage.geojson' });
  map.addSource('raw-manholes', { type: 'geojson', data: './Moddata/raw_manholes.geojson' });
  map.addSource('risk-zones', { type: 'geojson', data: './Moddata/contamination_risk_zones.geojson' });
  map.addSource('primary-drains', { type: 'geojson', data: './Moddata/mod-foundation_primarydrains.geojson' });
  map.addSource('secondary-drains', { type: 'geojson', data: './Moddata/mod-foundation_secondarydrains.geojson' });
  map.addSource('lakes-existing', { type: 'geojson', data: './Moddata/mod-foundation_lakes_existing.geojson' });
  map.addSource('lakes-lost', { type: 'geojson', data: './Moddata/mod-foundation_lakes_lost.geojson' });
  map.addSource('ward-risk', { type: 'geojson', data: './Moddata/ward_risk_thematic.geojson' });
  map.addSource('slums', { type: 'geojson', data: './Moddata/slums.geojson' });
  map.addSource('audits', { type: 'geojson', data: './Moddata/audits.geojson' });

  // Add layers (initially hidden)
  map.addLayer({
    id: 'layer-raw-water', type: 'line', source: 'raw-water', layout: { 'visibility': 'none' },
    paint: { 'line-color': '#38bdf8', 'line-width': 1.5, 'line-opacity': 0.7 }
  });
  map.addLayer({
    id: 'layer-raw-sewage', type: 'line', source: 'raw-sewage', layout: { 'visibility': 'none' },
    paint: { 'line-color': '#a855f7', 'line-width': 1.5, 'line-opacity': 0.7 }
  });
  map.addLayer({
    id: 'layer-raw-manholes', type: 'circle', source: 'raw-manholes', layout: { 'visibility': 'none' },
    paint: { 'circle-color': '#f87171', 'circle-radius': 2, 'circle-opacity': 0.8 }
  });
  map.addLayer({
    id: 'layer-risk-heatmap', type: 'heatmap', source: 'risk-zones', layout: { 'visibility': 'none' },
    paint: {
      'heatmap-weight': 1,
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 10, 1, 15, 3],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0, 'rgba(6, 182, 212, 0)',
        0.2, 'rgba(6, 182, 212, 0.2)',
        0.4, 'rgba(6, 182, 212, 0.5)',
        0.6, '#06b6d4',
        0.8, '#22d3ee',
        1, '#ffffff'
      ],
      'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 10, 3, 15, 10],
      'heatmap-opacity': 0.9
    }
  });
  map.addLayer({
    id: 'layer-primary-drains', type: 'line', source: 'primary-drains', layout: { 'visibility': 'none' },
    paint: { 'line-color': '#1d4ed8', 'line-width': 3, 'line-opacity': 0.8 }
  });
  map.addLayer({
    id: 'layer-secondary-drains', type: 'line', source: 'secondary-drains', layout: { 'visibility': 'none' },
    paint: { 'line-color': '#60a5fa', 'line-width': 1.5, 'line-opacity': 0.6 }
  });
  map.addLayer({
    id: 'layer-lakes-existing', type: 'fill', source: 'lakes-existing', layout: { 'visibility': 'none' },
    paint: { 'fill-color': '#2563eb', 'fill-opacity': 0.6, 'fill-outline-color': '#1e40af' }
  });
  map.addLayer({
    id: 'layer-lakes-lost', type: 'fill', source: 'lakes-lost', layout: { 'visibility': 'none' },
    paint: { 'fill-color': '#475569', 'fill-opacity': 0.5, 'fill-outline-color': '#334155' }
  });
  map.addLayer({
    id: 'layer-ward-risk', type: 'fill', source: 'ward-risk', layout: { 'visibility': 'none' },
    paint: {
      'fill-color': [
        'interpolate', ['linear'], ['get', 'risk_count'],
        0, 'rgba(254, 240, 138, 0.1)',
        50, 'rgba(254, 240, 138, 0.6)',
        100, 'rgba(249, 115, 22, 0.7)',
        200, 'rgba(239, 68, 68, 0.8)',
        320, 'rgba(153, 27, 27, 0.9)'
      ],
      'fill-opacity': 0.8,
      'fill-outline-color': '#ffffff'
    }
  });
  map.addLayer({
    id: 'layer-slums', type: 'fill', source: 'slums', layout: { 'visibility': 'none' },
    paint: { 'fill-color': '#f43f5e', 'fill-opacity': 0.5, 'fill-outline-color': '#be123c' }
  });
  map.addLayer({
    id: 'layer-audits', type: 'circle', source: 'audits', layout: { 'visibility': 'none' },
    paint: { 'circle-color': '#f472b6', 'circle-radius': 8, 'circle-stroke-width': 2, 'circle-stroke-color': '#ffffff' }
  });

  // Setup Intersection Observer for Scrollytelling
  let activeChapterName = 'chapter-1';

  function setActiveChapter(chapterName) {
    if (chapterName === activeChapterName) return;

    map.flyTo({
      center: chapters[chapterName].center,
      zoom: chapters[chapterName].zoom,
      pitch: chapters[chapterName].pitch,
      bearing: chapters[chapterName].bearing,
      essential: true,
      duration: 2500 // Smooth transition
    });

    // Toggle layers
    allLayers.forEach(layer => {
      const visibility = chapters[chapterName].layers.includes(layer) ? 'visible' : 'none';
      map.setLayoutProperty(layer, 'visibility', visibility);
    });

    document.getElementById(chapterName).classList.add('active');
    document.getElementById(activeChapterName).classList.remove('active');

    activeChapterName = chapterName;
  }

  // Use IntersectionObserver
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        setActiveChapter(entry.target.id);
      }
    });
  }, {
    root: null,
    rootMargin: '-30% 0px -60% 0px', // Trigger when section is in middle of viewport
    threshold: 0
  });

  document.querySelectorAll('.step').forEach(step => {
    observer.observe(step);
  });
  
  // Set initial state
  setActiveChapter('chapter-1');
});
