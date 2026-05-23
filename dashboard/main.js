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

const formatMeasurement = (value, unit = 'mg/L') => {
  if (value === null || value === undefined || value === '') return 'N/A';
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toLocaleString()}${unit ? ` ${unit}` : ''}` : 'N/A';
};

const initLayers = () => {
  // --- SOURCES ---
  map.addSource('risk-zones', { type: 'geojson', data: './contamination_risk_zones.geojson' });
  map.addSource('primary-drains', { type: 'geojson', data: './Moddata/mod-foundation_primarydrains.geojson' });
  map.addSource('secondary-drains', { type: 'geojson', data: './Moddata/mod-foundation_secondarydrains.geojson' });
  map.addSource('valley-systems', { type: 'geojson', data: './Moddata/mod-foundation_valley.geojson' });
  map.addSource('watershed-basins', { type: 'geojson', data: './Moddata/mod-foundation_valley_subbasins.geojson' });
  map.addSource('natural-stream-order', { type: 'geojson', data: './Moddata/mod-foundation_streamorder.geojson' });
  map.addSource('land-slopes', { type: 'geojson', data: './Moddata/bengaluru_slopes.geojson' });
  map.addSource('lakes-existing', { type: 'geojson', data: './Moddata/mod-foundation_lakes_existing.geojson' });
  map.addSource('lakes-lost', { type: 'geojson', data: './Moddata/mod-foundation_lakes_lost.geojson' });
  map.addSource('lake-water-quality', { type: 'geojson', data: './Moddata/lake_water_quality.geojson' });
  map.addSource('parks', { type: 'geojson', data: './Moddata/mod-foundation_parks.geojson' });
  map.addSource('audits', { type: 'geojson', data: './Moddata/audits.geojson' });
  map.addSource('groundwater-quality', { type: 'geojson', data: './Moddata/groundwater_quality.geojson' });
  map.addSource('raw-water', { type: 'geojson', data: './Moddata/raw_water.geojson' });
  map.addSource('raw-sewage', { type: 'geojson', data: './Moddata/raw_sewage.geojson' });
  map.addSource('raw-manholes', { type: 'geojson', data: './Moddata/raw_manholes.geojson' });
  map.addSource('ward-risk', { type: 'geojson', data: './Moddata/ward_risk_thematic.geojson' });

  // --- LAYERS ---
  
  // Land slope classes: natural terrain context for drainage alignment
  map.addLayer({
    id: 'layer-land-slopes',
    type: 'fill',
    source: 'land-slopes',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': [
        'match',
        ['get', 'slope'],
        '0-1%', '#d9f99d',
        '1-3%', '#bef264',
        '3-5%', '#fde047',
        '5-10%', '#fb923c',
        '10-15%', '#f97316',
        '15-35%', '#dc2626',
        '35 - 50%', '#7f1d1d',
        '#94a3b8'
      ],
      'fill-opacity': 0.22,
      'fill-outline-color': 'rgba(255,255,255,0.15)'
    }
  });

  // Valley systems: major natural drainage catchments
  map.addLayer({
    id: 'layer-valley-systems',
    type: 'fill',
    source: 'valley-systems',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': [
        'match',
        ['get', 'valley'],
        'Arkavathi Valley', 'rgba(34, 197, 94, 0.18)',
        'Hebbal Nagawara Valley', 'rgba(14, 165, 233, 0.18)',
        'Koramangala Challaghatta Valley', 'rgba(168, 85, 247, 0.18)',
        'Suvarnamukhi Valley', 'rgba(250, 204, 21, 0.16)',
        'Vrishabhavati Valley', 'rgba(249, 115, 22, 0.16)',
        'rgba(148, 163, 184, 0.14)'
      ],
      'fill-outline-color': '#e0f2fe'
    }
  });

  map.addLayer({
    id: 'layer-valley-boundaries',
    type: 'line',
    source: 'valley-systems',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#e0f2fe',
      'line-width': 2.2,
      'line-opacity': 0.9
    }
  });

  map.addLayer({
    id: 'layer-valley-labels',
    type: 'symbol',
    source: 'valley-systems',
    layout: {
      'visibility': 'none',
      'text-field': ['get', 'valley'],
      'text-font': ['Noto Sans Regular'],
      'text-size': 12,
      'text-max-width': 14,
      'text-allow-overlap': false
    },
    paint: {
      'text-color': '#e0f2fe',
      'text-halo-color': '#0f172a',
      'text-halo-width': 1.4
    }
  });

  // Watershed/sub-basin boundaries: finer natural drainage divisions
  map.addLayer({
    id: 'layer-watershed-basins',
    type: 'line',
    source: 'watershed-basins',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#facc15',
      'line-width': 1.7,
      'line-dasharray': [2, 2],
      'line-opacity': 0.85
    }
  });

  // Natural stream order: inferred flow paths for comparing SWD alignment
  map.addLayer({
    id: 'layer-natural-stream-order',
    type: 'line',
    source: 'natural-stream-order',
    layout: { 'visibility': 'none' },
    paint: {
      'line-color': '#22d3ee',
      'line-width': [
        'interpolate',
        ['linear'],
        ['to-number', ['get', 'ORD_FLOW']],
        1, 0.8,
        6, 2.2,
        11, 4
      ],
      'line-opacity': 0.8
    }
  });

  // Parks & Wetlands
  map.addLayer({
    id: 'layer-parks',
    type: 'fill',
    source: 'parks',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#16a34a',
      'fill-opacity': 0.2,
      'fill-outline-color': '#15803d'
    }
  });

  // Lost Lakes
  map.addLayer({
    id: 'layer-lakes-lost',
    type: 'fill',
    source: 'lakes-lost',
    layout: { 'visibility': 'none' },
    paint: {
      'fill-color': '#4b5563',
      'fill-opacity': 0.4,
      'fill-outline-color': '#9ca3af'
    }
  });

  // Existing Lakes
  map.addLayer({
    id: 'layer-lakes-existing',
    type: 'fill',
    source: 'lakes-existing',
    paint: {
      'fill-color': '#3b82f6',
      'fill-opacity': 0.5,
      'fill-outline-color': '#60a5fa'
    }
  });

  // Latest Lake Water Quality (PDF-derived pollution levels)
  map.addLayer({
    id: 'layer-lake-water-quality',
    type: 'fill',
    source: 'lake-water-quality',
    paint: {
      'fill-color': [
        'match',
        ['get', 'pollution_level'],
        'Severe', '#dc2626',
        'High', '#f97316',
        'Moderate', '#facc15',
        'Low', '#22c55e',
        '#94a3b8'
      ],
      'fill-opacity': 0.62,
      'fill-outline-color': '#ffffff'
    }
  });

  // Labels for PDF monitoring locations on matched lake geometries
  map.addLayer({
    id: 'layer-lake-water-quality-labels',
    type: 'symbol',
    source: 'lake-water-quality',
    minzoom: 10.5,
    layout: {
      'text-field': ['get', 'monitoring_location'],
      'text-font': ['Noto Sans Regular'],
      'text-size': [
        'interpolate',
        ['linear'],
        ['zoom'],
        10.5, 10,
        14, 13
      ],
      'text-max-width': 12,
      'text-allow-overlap': false,
      'text-ignore-placement': false
    },
    paint: {
      'text-color': '#f8fafc',
      'text-halo-color': '#0f172a',
      'text-halo-width': 1.5,
      'text-halo-blur': 0.5
    }
  });

  // Secondary Drains
  map.addLayer({
    id: 'layer-secondary-drains',
    type: 'line',
    source: 'secondary-drains',
    paint: {
      'line-color': '#60a5fa',
      'line-width': 1.5,
      'line-opacity': 0.8
    }
  });

  // Primary Drains
  map.addLayer({
    id: 'layer-primary-drains',
    type: 'line',
    source: 'primary-drains',
    paint: {
      'line-color': '#1d4ed8',
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

  // Groundwater Quality (Measured Well Samples)
  map.addLayer({
    id: 'layer-groundwater-quality',
    type: 'circle',
    source: 'groundwater-quality',
    paint: {
      'circle-color': [
        'match',
        ['get', 'status'],
        'High concern', '#ef4444',
        'Caution', '#f59e0b',
        'Within limits', '#22c55e',
        '#94a3b8'
      ],
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        9, 5,
        14, 9
      ],
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 1.5,
      'circle-opacity': 0.9
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
      'line-color': '#38bdf8', // Light Blue
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

  // Add click interaction for Groundwater Quality samples
  map.on('click', 'layer-groundwater-quality', (e) => {
    const coordinates = e.features[0].geometry.coordinates.slice();
    const props = e.features[0].properties;
    const statusColor = {
      'High concern': '#ef4444',
      'Caution': '#f59e0b',
      'Within limits': '#22c55e'
    }[props.status] || 'var(--accent-cyan)';

    let popupContent = `<div class="popup-custom">`;
    popupContent += `<h4>Groundwater Quality</h4>`;
    popupContent += `<div class="popup-details">`;
    popupContent += `<p><strong>Village:</strong> ${props.village || 'Unknown'}</p>`;
    popupContent += `<p><strong>Taluk:</strong> ${props.taluk || 'Unknown'}</p>`;
    popupContent += `<p><strong>Status:</strong> <span style="color:${statusColor}; font-weight:bold;">${props.status || 'N/A'}</span></p>`;
    popupContent += `<p><strong>Issues:</strong> ${props.issues || 'None'}</p>`;
    popupContent += `<hr style="border: 0; border-top: 1px solid var(--border-color); margin: 8px 0;">`;
    popupContent += `<p><strong>Nitrate:</strong> ${formatMeasurement(props.nitrate_mg_l)}</p>`;
    popupContent += `<p><strong>Fluoride:</strong> ${formatMeasurement(props.fluoride_mg_l)}</p>`;
    popupContent += `<p><strong>Iron:</strong> ${formatMeasurement(props.iron_mg_l)}</p>`;
    popupContent += `<p><strong>Total Hardness:</strong> ${formatMeasurement(props.hardness_mg_l)}</p>`;
    popupContent += `</div></div>`;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '300px' })
      .setLngLat(coordinates)
      .setHTML(popupContent)
      .addTo(map);
  });

  // Change cursor on hover for groundwater samples
  map.on('mouseenter', 'layer-groundwater-quality', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-groundwater-quality', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click interaction for latest lake water-quality report
  map.on('click', 'layer-lake-water-quality', (e) => {
    const props = e.features[0].properties;
    const levelColor = {
      'Severe': '#dc2626',
      'High': '#f97316',
      'Moderate': '#facc15',
      'Low': '#22c55e'
    }[props.pollution_level] || 'var(--accent-cyan)';

    let popupContent = `<div class="popup-custom">`;
    popupContent += `<h4>${props.monitoring_location || props.matched_lake_name || 'Lake Water Quality'}</h4>`;
    popupContent += `<div class="popup-details">`;
    popupContent += `<p><strong>Report:</strong> ${props.report_month_name || ''} ${props.report_year || ''}</p>`;
    popupContent += `<p><strong>Matched Map Lake:</strong> ${props.matched_lake_name || 'N/A'}</p>`;
    popupContent += `<p><strong>Pollution Level:</strong> <span style="color:${levelColor}; font-weight:bold;">${props.pollution_level || 'N/A'}</span></p>`;
    popupContent += `<p><strong>Main Drivers:</strong> ${props.pollution_drivers || 'None'}</p>`;
    popupContent += `<hr style="border: 0; border-top: 1px solid var(--border-color); margin: 8px 0;">`;
    popupContent += `<p><strong>Dissolved O2:</strong> ${formatMeasurement(props.dissolved_oxygen_mg_l)}</p>`;
    popupContent += `<p><strong>BOD:</strong> ${formatMeasurement(props.bod_mg_l)}</p>`;
    popupContent += `<p><strong>COD:</strong> ${formatMeasurement(props.cod_mg_l)}</p>`;
    popupContent += `<p><strong>Fecal Coliform:</strong> ${formatMeasurement(props.fecal_coliform_mpn_100ml, 'MPN/100ml')}</p>`;
    popupContent += `<p><strong>Total Coliform:</strong> ${formatMeasurement(props.total_coliform_mpn_100ml, 'MPN/100ml')}</p>`;
    popupContent += `<p><strong>Turbidity:</strong> ${formatMeasurement(props.turbidity_ntu, 'NTU')}</p>`;
    popupContent += `<p><strong>pH:</strong> ${formatMeasurement(props.ph, '')}</p>`;
    popupContent += `</div></div>`;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '320px' })
      .setLngLat(e.lngLat)
      .setHTML(popupContent)
      .addTo(map);
  });

  // Change cursor on hover for lake water-quality polygons
  map.on('mouseenter', 'layer-lake-water-quality', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-lake-water-quality', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click interaction for valley systems
  map.on('click', 'layer-valley-systems', (e) => {
    const props = e.features[0].properties;
    const popupContent = `
      <div class="popup-custom">
        <h4>${props.valley || 'Valley System'}</h4>
        <div class="popup-details">
          <p><strong>Basin ID:</strong> ${props.Basin_ID || 'N/A'}</p>
          <p><strong>HydroBASINS ID:</strong> ${props.HYBAS_ID || 'N/A'}</p>
          <p><strong>Upstream Area:</strong> ${formatMeasurement(props.UP_AREA, 'sq km')}</p>
          <p><strong>Sub Area:</strong> ${formatMeasurement(props.SUB_AREA, 'sq km')}</p>
        </div>
      </div>
    `;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '280px' })
      .setLngLat(e.lngLat)
      .setHTML(popupContent)
      .addTo(map);
  });

  map.on('mouseenter', 'layer-valley-systems', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-valley-systems', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click interaction for slope classes
  map.on('click', 'layer-land-slopes', (e) => {
    const props = e.features[0].properties;
    const popupContent = `
      <div class="popup-custom">
        <h4>Land Slope</h4>
        <div class="popup-details">
          <p><strong>Slope Class:</strong> ${props.slope || 'N/A'}</p>
          <p><strong>Description:</strong> ${props.description || 'N/A'}</p>
          <p><strong>Slope Code:</strong> ${props.slope_code || 'N/A'}</p>
        </div>
      </div>
    `;

    new maplibregl.Popup({ className: 'custom-popup', maxWidth: '260px' })
      .setLngLat(e.lngLat)
      .setHTML(popupContent)
      .addTo(map);
  });

  map.on('mouseenter', 'layer-land-slopes', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'layer-land-slopes', () => {
    map.getCanvas().style.cursor = '';
  });

  // Add click interaction for Ward Risk Choropleth
  map.on('click', 'layer-ward-risk', (e) => {
    const props = e.features[0].properties;

    let popupContent = `<div class="popup-custom">`;
    popupContent += `<h4>Ward: ${props.ward_name || 'Unknown'}</h4>`;
    
    popupContent += `<div class="popup-details">`;
    popupContent += `<p><strong>Contamination Risk Points:</strong> <span style="color:var(--accent-cyan); font-weight:bold;">${props.risk_count || 0}</span></p>`;
    
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
    'toggle-valley-systems': ['layer-valley-systems', 'layer-valley-boundaries', 'layer-valley-labels'],
    'toggle-watershed-basins': ['layer-watershed-basins'],
    'toggle-natural-stream-order': ['layer-natural-stream-order'],
    'toggle-land-slopes': ['layer-land-slopes'],
    'toggle-lakes-existing': ['layer-lakes-existing'],
    'toggle-lakes-lost': ['layer-lakes-lost'],
    'toggle-lake-water-quality': ['layer-lake-water-quality', 'layer-lake-water-quality-labels'],
    'toggle-parks': ['layer-parks'],
    'toggle-audits': ['layer-audits'],
    'toggle-groundwater-quality': ['layer-groundwater-quality'],
    'toggle-risk': ['layer-risk-heatmap'],
    'toggle-ward-risk': ['layer-ward-risk'],
    'toggle-raw-water': ['layer-raw-water'],
    'toggle-raw-sewage': ['layer-raw-sewage'],
    'toggle-raw-manholes': ['layer-raw-manholes']
  };

  for (const [checkboxId, layerIds] of Object.entries(toggles)) {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
      const initialVisibility = checkbox.checked ? 'visible' : 'none';
      layerIds.forEach(layerId => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, 'visibility', initialVisibility);
        }
      });

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
});
