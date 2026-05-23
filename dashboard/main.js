import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// Initialize MapLibre GL JS
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  center: [77.5946, 12.9716],
  zoom: 11,
  pitch: 45,
  bearing: 0,
  antialias: true
});

map.addControl(new maplibregl.NavigationControl({
  visualizePitch: true
}), 'bottom-right');

const initLayers = () => {
  // --- SOURCES ---
  map.addSource('risk-zones', { type: 'geojson', data: './contamination_risk_zones.geojson' });
  map.addSource('primary-drains', { type: 'geojson', data: './Moddata/mod-foundation_primarydrains.geojson' });
  map.addSource('secondary-drains', { type: 'geojson', data: './Moddata/mod-foundation_secondarydrains.geojson' });
  map.addSource('lakes-existing', { type: 'geojson', data: './Moddata/mod-foundation_lakes_existing.geojson' });
  map.addSource('lakes-lost', { type: 'geojson', data: './Moddata/mod-foundation_lakes_lost.geojson' });
  map.addSource('parks', { type: 'geojson', data: './Moddata/mod-foundation_parks.geojson' });
  map.addSource('audits', { type: 'geojson', data: './Moddata/audits.geojson' });
  map.addSource('raw-water', { type: 'geojson', data: './Moddata/raw_water.geojson' });
  map.addSource('raw-sewage', { type: 'geojson', data: './Moddata/raw_sewage.geojson' });
  map.addSource('raw-manholes', { type: 'geojson', data: './Moddata/raw_manholes.geojson' });
  map.addSource('ward-risk', { type: 'geojson', data: './Moddata/ward_risk_thematic.geojson' });
  map.addSource('slums', { type: 'geojson', data: './Moddata/slums.geojson' });

  // --- LAYERS ---
  
  // Parks & Wetlands
  map.addLayer({
    id: 'layer-parks',
    type: 'fill',
    source: 'parks',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#22c55e', // Solid Green
      'fill-opacity': 0.5,
      'fill-outline-color': '#166534'
    }
  });

  // Lost Lakes
  map.addLayer({
    id: 'layer-lakes-lost',
    type: 'fill',
    source: 'lakes-lost',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#64748b', // Slate
      'fill-opacity': 0.5,
      'fill-outline-color': '#334155'
    }
  });

  // Existing Lakes
  map.addLayer({
    id: 'layer-lakes-existing',
    type: 'fill',
    source: 'lakes-existing',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#0d9488', // Teal
      'fill-opacity': 0.6,
      'fill-outline-color': '#115e59'
    }
  });

  // Secondary Drains
  map.addLayer({
    id: 'layer-secondary-drains',
    type: 'line',
    source: 'secondary-drains',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#0ea5e9', // Sky Blue
      'line-width': 1.5,
      'line-opacity': 0.8
    }
  });

  // Primary Drains
  map.addLayer({
    id: 'layer-primary-drains',
    type: 'line',
    source: 'primary-drains',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#1d4ed8', // Navy Blue
      'line-width': 3,
      'line-opacity': 0.9
    }
  });

  // Contamination Risk (Heatmap along pipelines)
  map.addLayer({
    id: 'layer-risk-heatmap',
    type: 'heatmap',
    source: 'risk-zones',
    paint: {
      // Increase the heatmap weight based on density
      'heatmap-weight': 1,
      // Increase the heatmap color weight weight by zoom level
      // heatmap-intensity is a multiplier on top of heatmap-weight
      'heatmap-intensity': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10, 1,
        15, 3
      ],
      // Color ramp from transparent cyan to solid bright cyan/white
      'heatmap-color': [
        'interpolate',
        ['linear'],
        ['heatmap-density'],
        0, 'rgba(6, 182, 212, 0)',
        0.2, 'rgba(6, 182, 212, 0.2)',
        0.4, 'rgba(6, 182, 212, 0.5)',
        0.6, '#06b6d4',
        0.8, '#22d3ee',
        1, '#ffffff'
      ],
      // Adjust the heatmap radius by zoom level
      'heatmap-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10, 3,
        15, 10
      ],
      'heatmap-opacity': 0.9
    }
  });

  // Citizen Audits (Points)
  map.addLayer({
    id: 'layer-audits',
    type: 'circle',
    source: 'audits',
    paint: {
      'circle-color': '#ec4899', // Pink
      'circle-radius': 5,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#ffffff'
    }
  });

  // Raw Manholes (Points)
  map.addLayer({
    id: 'layer-raw-manholes',
    type: 'circle',
    source: 'raw-manholes',
    layout: { 'visibility': 'none' },
    paint: {
      'circle-color': '#f59e0b', // Amber
      'circle-radius': 2,
      'circle-opacity': 0.8
    }
  });

  // Raw Sewage (Lines)
  map.addLayer({
    id: 'layer-raw-sewage',
    type: 'line',
    source: 'raw-sewage',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#a855f7', // Purple
      'line-width': 1.5,
      'line-opacity': 0.7
    }
  });

  // Raw Water (Lines)
  map.addLayer({
    id: 'layer-raw-water',
    type: 'line',
    source: 'raw-water',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#3b82f6', // Bright Blue
      'line-width': 1.5,
      'line-opacity': 0.7
    }
  });


  // Ward Risk Choropleth
  map.addLayer({
    id: 'layer-ward-risk',
    type: 'fill',
    source: 'ward-risk',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': [
        'interpolate',
        ['linear'],
        ['get', 'risk_count'],
        0, 'rgba(254, 240, 138, 0.1)',   // Very transparent yellow
        50, 'rgba(254, 240, 138, 0.6)',  // Yellow
        100, 'rgba(249, 115, 22, 0.7)',  // Orange
        200, 'rgba(239, 68, 68, 0.8)',   // Red
        320, 'rgba(153, 27, 27, 0.9)'    // Dark Red
      ],
      'fill-opacity': 0.8,
      'fill-outline-color': '#ffffff'
    }
  }, 'layer-risk-heatmap'); // Place underneath the risk heatmap points if possible

  // Slum Boundaries
  map.addLayer({
    id: 'layer-slums',
    type: 'fill',
    source: 'slums',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#e11d48', // Rose
      'fill-opacity': 0.5,
      'fill-outline-color': '#9f1239' // Dark Rose
    }
  });

  // Cinematic FlyTo
  map.flyTo({
    center: [77.5946, 12.9716],
    zoom: 11.5,
    pitch: 45,
    speed: 0.2,
    curve: 1,
    easing(t) { return t; }
  });
  
  setupToggleControls();

  // Add click interaction for Citizen Audits
  map.on('click', 'layer-audits', (e) => {
    const coordinates = e.features[0].geometry.coordinates.slice();
    const props = e.features[0].properties;

    // Ensure the popup appears over the correct copy of the feature
    while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
      coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
    }

    let popupContent = `<div class="popup-custom">`;
    popupContent += `<h4>Citizen Audit Report</h4>`;
    
    // Add image if available
    if (props.water_pic && props.water_pic !== 'null' && props.water_pic !== '') {
      const imgUrl = `https://pub-4d67c97c1d2843adbeffa3b98cd45d19.r2.dev/${props.water_pic}`;
      popupContent += `<img src="${imgUrl}" alt="Water condition" class="popup-img" />`;
    }
    
    popupContent += `<div class="popup-details">`;
    popupContent += `<p><strong>Contamination:</strong> ${props.water_contamination || 'N/A'}</p>`;
    popupContent += `<p><strong>Color:</strong> ${props.water_colour || 'N/A'}</p>`;
    popupContent += `<p><strong>Solid Waste:</strong> ${props.sw_inside_type || 'None'}</p>`;
    popupContent += `</div></div>`;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '300px' })
      .setLngLat(coordinates)
      .setHTML(popupContent)
      .addTo(map);
  });

  // Change cursor on hover for audits
  map.on('mouseenter', 'layer-audits', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-audits', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click interaction for Ward Risk Choropleth
  map.on('click', 'layer-ward-risk', (e) => {
    const props = e.features[0].properties;

    let popupContent = `<div class="popup-custom">`;
    popupContent += `<h4>Ward: ${props.ward_name || 'Unknown'}</h4>`;
    
    popupContent += `<div class="popup-details">`;
    popupContent += `<p><strong>Contamination Risk Points:</strong> <span style="color:var(--accent-cyan); font-weight:bold;">${props.risk_count || 0}</span></p>`;
    
    if (props.slum_count > 0) {
      popupContent += `<p><strong>Number of Slums:</strong> <span style="color:#f43f5e; font-weight:bold;">${props.slum_count}</span></p>`;
    }
    
    // Socioeconomic Data
    if (props.TOT_P) {
      popupContent += `<hr style="border: 0; border-top: 1px solid var(--border-color); margin: 8px 0;">`;
      popupContent += `<p><strong>Total Population:</strong> ${Number(props.TOT_P).toLocaleString()}</p>`;
      popupContent += `<p><strong>SC Population:</strong> ${props.SC_Percent || 0}%</p>`;
      popupContent += `<p><strong>ST Population:</strong> ${props.ST_Percent || 0}%</p>`;
    } else {
      popupContent += `<p><em>Socioeconomic data unavailable</em></p>`;
    }
    popupContent += `</div></div>`;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '250px' })
      .setLngLat(e.lngLat)
      .setHTML(popupContent)
      .addTo(map);
  });

  // Change cursor on hover for wards
  map.on('mouseenter', 'layer-ward-risk', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-ward-risk', () => {
    map.getCanvas().style.cursor = '';
  });
};

if (map.loaded()) {
  initLayers();
} else {
  map.on('load', initLayers);
}

// Set up UI Toggles
function setupToggleControls() {
  const toggles = {
    'toggle-primary-drains': ['layer-primary-drains'],
    'toggle-secondary-drains': ['layer-secondary-drains'],
    'toggle-lakes-existing': ['layer-lakes-existing'],
    'toggle-lakes-lost': ['layer-lakes-lost'],
    'toggle-parks': ['layer-parks'],
    'toggle-audits': ['layer-audits'],
    'toggle-risk': ['layer-risk-heatmap'],
    'toggle-ward-risk': ['layer-ward-risk'],
    'toggle-slums': ['layer-slums'],
    'toggle-raw-water': ['layer-raw-water'],
    'toggle-raw-sewage': ['layer-raw-sewage'],
    'toggle-raw-manholes': ['layer-raw-manholes']
  };

  for (const [checkboxId, layerIds] of Object.entries(toggles)) {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      checkbox.addEventListener('change', (e) => {
        const visibility = e.target.checked ? 'visible' : 'none';
        layerIds.forEach(layerId => {
          if (map.getLayer(layerId)) {
            map.setLayoutProperty(layerId, 'visibility', visibility);
          }
        });
      });
    }
  }
}

// Animate the metric counter
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const easeOut = progress * (2 - progress);
    const current = Math.floor(easeOut * (end - start) + start);
    obj.innerHTML = current.toLocaleString();
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
  const counter = document.getElementById('risk-count');
  if(counter) animateValue(counter, 0, 25210, 2000);

  // Load and render Ward Rankings
  fetch('./Moddata/ward_rankings.json')
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('ward-ranking-list');
      if (!list) return;
      list.innerHTML = '';
      
      data.slice(0, 50).forEach((ward, index) => {
        if (!ward.ward_name || ward.risk_count === 0) return;
        
        const li = document.createElement('li');
        li.style.padding = '8px 12px';
        li.style.borderBottom = '1px solid var(--border-color)';
        li.style.display = 'flex';
        li.style.justifyContent = 'space-between';
        li.style.alignItems = 'center';
        li.style.fontSize = '0.85rem';
        
        let rankColor = '#ef4444'; // Red
        let bgOpacity = '0.1';
        
        if (index === 0) { rankColor = '#fca5a5'; bgOpacity = '0.3'; } // Highlight top 1
        else if (index < 3) { rankColor = '#f87171'; bgOpacity = '0.15'; } // Highlight top 3
        
        li.innerHTML = `
          <span style="font-weight: 500; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%;" title="${ward.ward_name}">${index + 1}. ${ward.ward_name}</span>
          <span style="font-weight: bold; color: ${rankColor}; background: rgba(239, 68, 68, ${bgOpacity}); padding: 2px 6px; border-radius: 4px;" title="${ward.risk_count} Risk Intersections">${ward.risk_count}</span>
        `;
        list.appendChild(li);
      });
      
      if (list.lastChild) {
        list.lastChild.style.borderBottom = 'none';
      }
    })
    .catch(err => console.error('Error loading ward rankings:', err));
});
