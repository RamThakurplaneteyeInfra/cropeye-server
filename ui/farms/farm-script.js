document.addEventListener('DOMContentLoaded', function() {
    // API Endpoints
    const API_BASE_URL = 'http://localhost:8000/api';
    const API_FARMS = `${API_BASE_URL}/farms/`;
    const API_FARM_PLOTS = `${API_BASE_URL}/farm-plots/`;
    const API_SOIL_TYPES = `${API_BASE_URL}/soil-types/`;
    const API_CROP_TYPES = `${API_BASE_URL}/crop-types/`;
    const API_PLANTATION_TYPES = `${API_BASE_URL}/farms/plantation-types/`;
    const API_PLANTING_METHODS = `${API_BASE_URL}/farms/planting-methods/`;
    
    // Token from localStorage
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '../index.html';
    }
    
    // DOM Elements
    const farmRegSection = document.getElementById('farm-registration-section');
    const farmsListSection = document.getElementById('farms-list-section');
    const farmDetailsSection = document.getElementById('farm-details-section');
    
    const viewFarmsBtn = document.getElementById('view-farms-btn');
    const addFarmBtn = document.getElementById('add-farm-btn');
    const backToFarmsBtn = document.getElementById('back-to-farms-btn');
    
    const farmForm = document.getElementById('farm-registration-form');
    const locationSearch = document.getElementById('location-search');
    const searchBtn = document.getElementById('search-btn');
    
    const locationCoordinates = document.getElementById('location-coordinates');
    const boundaryVertices = document.getElementById('boundary-vertices');
    const locationLat = document.getElementById('location-lat');
    const locationLng = document.getElementById('location-lng');
    const boundaryGeoJSON = document.getElementById('boundary-geojson');
    
    // Tab Navigation
    const formTabs = document.querySelectorAll('.form-tab');
    const nextButtons = document.querySelectorAll('.next-tab');
    const prevButtons = document.querySelectorAll('.prev-tab');
    
    // Maps
    let farmMap, farmsMap, plotsMap, sensorsMap;
    let drawnItems, locationMarker;
    
    // Initialize maps
    initMaps();
    
    // Load reference data
    loadSoilTypes();
    loadPlantationTypes();
    loadPlantingMethods();
    
    // Event Listeners
    formTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            activateTab(tabId);
        });
    });
    
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            const nextTab = this.getAttribute('data-next');
            activateTab(nextTab);
        });
    });
    
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            const prevTab = this.getAttribute('data-prev');
            activateTab(prevTab);
        });
    });
    
    viewFarmsBtn.addEventListener('click', showFarmsList);
    addFarmBtn.addEventListener('click', showFarmRegistration);
    backToFarmsBtn.addEventListener('click', showFarmsList);
    
    searchBtn.addEventListener('click', searchLocation);
    
    farmForm.addEventListener('submit', submitFarmForm);
    
    // Irrigation type change handler
    const irrigationTypeSelect = document.getElementById('irrigation-type');
    if (irrigationTypeSelect) {
        irrigationTypeSelect.addEventListener('change', handleIrrigationTypeChange);
        
        // Initialize irrigation fields display
        setTimeout(() => {
            handleIrrigationTypeChange();
        }, 100);
    }
    
    // Spacing calculation handler
    const spacingAInput = document.getElementById('spacing-a');
    const spacingBInput = document.getElementById('spacing-b');
    const areaSizeInput = document.getElementById('farm-area');
    const plantsCalculation = document.getElementById('plants-calculation');
    
    if (spacingAInput && spacingBInput && areaSizeInput && plantsCalculation) {
        spacingAInput.addEventListener('input', calculatePlants);
        spacingBInput.addEventListener('input', calculatePlants);
        areaSizeInput.addEventListener('input', calculatePlants);
    }
    
    // Add Plantation Type button
    const addPlantationTypeBtn = document.getElementById('add-plantation-type-btn');
    if (addPlantationTypeBtn) {
        addPlantationTypeBtn.addEventListener('click', function() {
            showAddPlantationTypeModal();
        });
    }
    
    // Add Planting Method button
    const addPlantingMethodBtn = document.getElementById('add-planting-method-btn');
    if (addPlantingMethodBtn) {
        addPlantingMethodBtn.addEventListener('click', function() {
            showAddPlantingMethodModal();
        });
    }
    
    // Irrigation Type Change Handler
    function handleIrrigationTypeChange() {
        const irrigationType = irrigationTypeSelect.value;
        const floodFields = document.getElementById('flood-irrigation-fields');
        const dripFields = document.getElementById('drip-irrigation-fields');
        
        // Hide all irrigation-specific fields
        document.querySelectorAll('.irrigation-specific-fields').forEach(field => {
            field.style.display = 'none';
        });
        
        // Show relevant fields based on irrigation type
        if (irrigationType === 'flood') {
            if (floodFields) {
                floodFields.style.display = 'block';
            }
        } else if (irrigationType === 'drip') {
            if (dripFields) {
                dripFields.style.display = 'block';
            }
        }
    }
    
    // Plants Calculation Function
    function calculatePlants() {
        const spacingA = parseFloat(spacingAInput.value) || 0;
        const spacingB = parseFloat(spacingBInput.value) || 0;
        const areaSize = parseFloat(areaSizeInput.value) || 0;
        
        
        if (spacingA > 0 && spacingB > 0 && areaSize > 0) {
            // Convert area from acres to square feet
            const areaSqFt = areaSize * 43560;
            
            // Calculate plants using formula: total area * 43560 / (spacing_a * spacing_b)
            // spacing_a and spacing_b are used as-is without any unit conversion
            const plants = Math.floor(areaSqFt / (spacingA * spacingB));
            
            plantsCalculation.textContent = `${plants.toLocaleString()} plants`;
            plantsCalculation.style.backgroundColor = '#e8f5e8';
            plantsCalculation.style.color = '#2e7d32';
        } else {
            plantsCalculation.textContent = 'Enter spacing values to calculate';
            plantsCalculation.style.backgroundColor = '#f5f5f5';
            plantsCalculation.style.color = '#666';
        }
    }
    
    // Tab Navigation Functions
    function activateTab(tabId) {
        // Hide all sections
        document.querySelectorAll('.form-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Deactivate all tabs
        formTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Activate the selected tab and section
        document.getElementById(`${tabId}-section`).classList.add('active');
        document.querySelector(`.form-tab[data-tab="${tabId}"]`).classList.add('active');
        
        // Special handling for the map
        if (tabId === 'location' && farmMap) {
            setTimeout(() => {
                farmMap.invalidateSize();
            }, 100);
        }
    }
    
    // Map Initialization
    function initMaps() {
        // Farm registration map
        farmMap = L.map('farm-map').setView([20.5937, 78.9629], 5);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(farmMap);
        
        // Setup draw control
        drawnItems = new L.FeatureGroup();
        farmMap.addLayer(drawnItems);
        
        const drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
                polyline: false,
                circle: false,
                rectangle: false,
                circlemarker: false,
                polygon: {
                    allowIntersection: false,
                    drawError: {
                        color: '#e1e100',
                        message: '<strong>Error:</strong> Polygon edges cannot cross!'
                    },
                    shapeOptions: {
                        color: '#3388ff'
                    }
                },
                marker: {
                    icon: new L.Icon.Default()
                }
            },
            edit: {
                featureGroup: drawnItems,
                poly: {
                    allowIntersection: false
                }
            }
        });
        farmMap.addControl(drawControl);
        
        // Event handlers for drawing
        farmMap.on(L.Draw.Event.CREATED, function(e) {
            const layer = e.layer;
            
            if (e.layerType === 'marker') {
                // Remove any existing location marker
                if (locationMarker) {
                    drawnItems.removeLayer(locationMarker);
                }
                locationMarker = layer;
                
                // Update coordinates display
                const latlng = layer.getLatLng();
                locationCoordinates.textContent = `Lat: ${latlng.lat.toFixed(6)}, Lng: ${latlng.lng.toFixed(6)}`;
                
                // Update hidden inputs
                locationLat.value = latlng.lat;
                locationLng.value = latlng.lng;
            } else if (e.layerType === 'polygon') {
                // Remove any existing polygons
                drawnItems.eachLayer(function(l) {
                    if (l instanceof L.Polygon) {
                        drawnItems.removeLayer(l);
                    }
                });
                
                // Update boundary vertices display
                const latlngs = layer.getLatLngs()[0];
                boundaryVertices.textContent = `${latlngs.length} points`;
                
                // Update hidden input
                boundaryGeoJSON.value = JSON.stringify(layer.toGeoJSON());
            }
            
            drawnItems.addLayer(layer);
        });
        
        farmMap.on(L.Draw.Event.EDITED, function(e) {
            const layers = e.layers;
            
            layers.eachLayer(function(layer) {
                if (layer instanceof L.Marker && locationMarker === layer) {
                    // Update coordinates display
                    const latlng = layer.getLatLng();
                    locationCoordinates.textContent = `Lat: ${latlng.lat.toFixed(6)}, Lng: ${latlng.lng.toFixed(6)}`;
                    
                    // Update hidden inputs
                    locationLat.value = latlng.lat;
                    locationLng.value = latlng.lng;
                } else if (layer instanceof L.Polygon) {
                    // Update boundary vertices display
                    const latlngs = layer.getLatLngs()[0];
                    boundaryVertices.textContent = `${latlngs.length} points`;
                    
                    // Update hidden input
                    boundaryGeoJSON.value = JSON.stringify(layer.toGeoJSON());
                }
            });
        });
        
        farmMap.on(L.Draw.Event.DELETED, function(e) {
            const layers = e.layers;
            
            layers.eachLayer(function(layer) {
                if (layer instanceof L.Marker && locationMarker === layer) {
                    locationMarker = null;
                    locationCoordinates.textContent = 'Not set';
                    locationLat.value = '';
                    locationLng.value = '';
                } else if (layer instanceof L.Polygon) {
                    boundaryVertices.textContent = '0 points';
                    boundaryGeoJSON.value = '';
                }
            });
        });
    }
    
    // Load Soil Types
    function loadSoilTypes() {
        fetch(API_SOIL_TYPES, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch soil types: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const soilTypeSelect = document.getElementById('soil-type');
            data.results.forEach(soilType => {
                const option = document.createElement('option');
                option.value = soilType.id;
                option.textContent = soilType.name;
                soilTypeSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading soil types:', error);
            alert('Failed to load soil types. Please try again later.');
        });
    }
    
    // Load plantation types into dropdown
    function loadPlantationTypes() {
        const select = document.getElementById('plantation-type');
        if (!select) return;
        
        fetch(`${API_PLANTATION_TYPES}?active_only=true`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch plantation types: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            select.innerHTML = '<option value="">Select Plantation Type</option>';
            const results = Array.isArray(data) ? data : (data.results || []);
            results.forEach(item => {
                const option = document.createElement('option');
                option.value = item.code || item.name.toLowerCase().replace(/\s+/g, '_');
                option.textContent = item.name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading plantation types:', error);
        });
    }
    
    // Load planting methods into dropdown
    function loadPlantingMethods() {
        const select = document.getElementById('planting-method');
        if (!select) return;
        
        fetch(`${API_PLANTING_METHODS}?active_only=true`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch planting methods: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            select.innerHTML = '<option value="">Select Planting Method</option>';
            const results = Array.isArray(data) ? data : (data.results || []);
            results.forEach(item => {
                const option = document.createElement('option');
                option.value = item.code || item.name.toLowerCase().replace(/\s+/g, '_');
                option.textContent = item.name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading planting methods:', error);
        });
    }
    
    // Function to show Add Plantation Type modal
    function showAddPlantationTypeModal() {
        const name = prompt('Enter Plantation Type Name:');
        if (!name || name.trim() === '') return;
        
        const code = prompt('Enter Plantation Type Code (optional):', name.toLowerCase().replace(/\s+/g, '_'));
        if (code === null) return;
        
        const description = prompt('Enter Description (optional):') || '';
        
        // Call API to create plantation type
        fetch(API_PLANTATION_TYPES, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name.trim(),
                code: code ? code.trim() : '',
                description: description.trim(),
                is_active: true
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(JSON.stringify(errorData));
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.id) {
                alert('Plantation Type added successfully!');
                loadPlantationTypes(); // Reload the dropdown
            } else {
                alert('Error: ' + (data.error || 'Failed to add plantation type'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            try {
                const errorData = JSON.parse(error.message);
                let errorMessages = '';
                for (const field in errorData) {
                    if (Array.isArray(errorData[field])) {
                        errorMessages += `${field}: ${errorData[field].join(', ')}\n`;
                    } else {
                        errorMessages += `${field}: ${errorData[field]}\n`;
                    }
                }
                alert(`Failed to add plantation type:\n${errorMessages}`);
            } catch (e) {
                alert('Failed to add plantation type. Please try again.');
            }
        });
    }
    
    // Function to show Add Planting Method modal
    function showAddPlantingMethodModal() {
        const name = prompt('Enter Planting Method Name:');
        if (!name || name.trim() === '') return;
        
        const code = prompt('Enter Planting Method Code (optional):', name.toLowerCase().replace(/\s+/g, '_'));
        if (code === null) return;
        
        const description = prompt('Enter Description (optional):') || '';
        
        // Call API to create planting method
        fetch(API_PLANTING_METHODS, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name.trim(),
                code: code ? code.trim() : '',
                description: description.trim(),
                is_active: true
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(JSON.stringify(errorData));
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.id) {
                alert('Planting Method added successfully!');
                loadPlantingMethods(); // Reload the dropdown
            } else {
                alert('Error: ' + (data.error || 'Failed to add planting method'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            try {
                const errorData = JSON.parse(error.message);
                let errorMessages = '';
                for (const field in errorData) {
                    if (Array.isArray(errorData[field])) {
                        errorMessages += `${field}: ${errorData[field].join(', ')}\n`;
                    } else {
                        errorMessages += `${field}: ${errorData[field]}\n`;
                    }
                }
                alert(`Failed to add planting method:\n${errorMessages}`);
            } catch (e) {
                alert('Failed to add planting method. Please try again.');
            }
        });
    }
    
    // Search for a location
    function searchLocation() {
        const searchText = locationSearch.value.trim();
        if (!searchText) {
            alert('Please enter a location to search for.');
            return;
        }
        
        // Use Nominatim for geocoding
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchText)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Geocoding failed: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                alert('No locations found with that name. Please try a different search.');
                return;
            }
            
            // Use the first result
            const result = data[0];
            const lat = parseFloat(result.lat);
            const lon = parseFloat(result.lon);
            
            // Update the map view
            farmMap.setView([lat, lon], 13);
            
            // Create a marker at this location
            if (locationMarker) {
                drawnItems.removeLayer(locationMarker);
            }
            
            locationMarker = L.marker([lat, lon]);
            drawnItems.addLayer(locationMarker);
            
            // Update coordinates display
            locationCoordinates.textContent = `Lat: ${lat.toFixed(6)}, Lng: ${lon.toFixed(6)}`;
            
            // Update hidden inputs
            locationLat.value = lat;
            locationLng.value = lon;
        })
        .catch(error => {
            console.error('Error searching location:', error);
            alert('Failed to search for location. Please try again later.');
        });
    }
    
    // Submit farm form
    function submitFarmForm(e) {
        e.preventDefault();
        
        // Validate form
        if (!validateFarmForm()) {
            return;
        }
        
        // Collect form data
        const formData = new FormData(farmForm);
        const farmData = {
            name: formData.get('name'),
            description: formData.get('description'),
            address: formData.get('address'),
            area_size: parseFloat(formData.get('area_size')),
            location_lat: parseFloat(formData.get('location_lat')),
            location_lng: parseFloat(formData.get('location_lng')),
            soil_type_id: formData.get('soil_type_id') || null,
            spacing_a: parseFloat(formData.get('spacing_a')),
            spacing_b: parseFloat(formData.get('spacing_b')),
            irrigation_type: formData.get('irrigation_type'),
            // Irrigation-specific fields
            motor_horsepower: formData.get('motor_horsepower') ? parseFloat(formData.get('motor_horsepower')) : null,
            pipe_width_inches: formData.get('pipe_width_inches') ? parseFloat(formData.get('pipe_width_inches')) : null,
            distance_motor_to_plot_m: formData.get('distance_motor_to_plot_m') ? parseFloat(formData.get('distance_motor_to_plot_m')) : null,
            plants_per_acre: formData.get('plants_per_acre') ? parseInt(formData.get('plants_per_acre')) : null,
            flow_rate_lph: formData.get('flow_rate_lph') ? parseFloat(formData.get('flow_rate_lph')) : null,
            emitters_count: formData.get('emitters_count') ? parseInt(formData.get('emitters_count')) : null
        };
        
        // Add boundary if provided
        if (formData.get('boundary')) {
            try {
                const boundary = JSON.parse(formData.get('boundary'));
                farmData.boundary_geojson = JSON.stringify(boundary.geometry);
            } catch (e) {
                console.error('Error parsing boundary GeoJSON:', e);
            }
        }
        
        // Submit data to API
        fetch(API_FARMS, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(farmData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(JSON.stringify(errorData));
                });
            }
            return response.json();
        })
        .then(data => {
            alert('Farm registered successfully!');
            resetFarmForm();
            showFarmsList();
            loadFarms();
        })
        .catch(error => {
            console.error('Error registering farm:', error);
            try {
                const errorData = JSON.parse(error.message);
                let errorMessages = '';
                for (const field in errorData) {
                    errorMessages += `${field}: ${errorData[field].join(', ')}\n`;
                }
                alert(`Failed to register farm:\n${errorMessages}`);
            } catch (e) {
                alert('Failed to register farm. Please try again later.');
            }
        });
    }
    
    // Validate farm form
    function validateFarmForm() {
        // Check if location is set
        if (!locationLat.value || !locationLng.value) {
            alert('Please set the main farm location by placing a marker on the map.');
            activateTab('location');
            return false;
        }
        
        return true;
    }
    
    // Reset farm form
    function resetFarmForm() {
        farmForm.reset();
        
        // Reset map layers
        if (drawnItems) {
            drawnItems.clearLayers();
        }
        
        locationMarker = null;
        locationCoordinates.textContent = 'Not set';
        boundaryVertices.textContent = '0 points';
        
        // Reset hidden inputs
        locationLat.value = '';
        locationLng.value = '';
        boundaryGeoJSON.value = '';
        
        // Reset to first tab
        activateTab('basic-info');
    }
    
    // Show farm registration section
    function showFarmRegistration() {
        farmRegSection.classList.remove('hidden');
        farmsListSection.classList.add('hidden');
        farmDetailsSection.classList.add('hidden');
        
        // Reset the form
        resetFarmForm();
        
        // Fix map display
        setTimeout(() => {
            if (farmMap) farmMap.invalidateSize();
        }, 100);
    }
    
    // Show farms list section
    function showFarmsList() {
        farmRegSection.classList.add('hidden');
        farmsListSection.classList.remove('hidden');
        farmDetailsSection.classList.add('hidden');
        
        // Load farms data
        loadFarms();
    }
    
    // Load user's farms
    function loadFarms() {
        // Initialize farms map if needed
        if (!farmsMap) {
            farmsMap = L.map('farms-map').setView([20.5937, 78.9629], 5);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(farmsMap);
        } else {
            // Clear existing markers
            farmsMap.eachLayer(layer => {
                if (layer instanceof L.Marker || layer instanceof L.Polygon) {
                    farmsMap.removeLayer(layer);
                }
            });
        }
        
        // Fix map display
        setTimeout(() => {
            if (farmsMap) farmsMap.invalidateSize();
        }, 100);
        
        // Fetch farms data
        fetch(`${API_FARMS}?my_farms=true`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch farms: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            populateFarmsTable(data.results);
            addFarmsToMap(data.results);
        })
        .catch(error => {
            console.error('Error loading farms:', error);
            alert('Failed to load farms. Please try again later.');
        });
    }
    
    // Populate farms table
    function populateFarmsTable(farms) {
        const tableBody = document.querySelector('#farms-table tbody');
        tableBody.innerHTML = '';
        
        if (farms.length === 0) {
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 6;
            cell.textContent = 'No farms found. Add a new farm to get started.';
            cell.style.textAlign = 'center';
            cell.style.padding = '20px 0';
            return;
        }
        
        farms.forEach(farm => {
            const row = tableBody.insertRow();
            
            const nameCell = row.insertCell();
            nameCell.textContent = farm.name;
            
            const areaCell = row.insertCell();
            areaCell.textContent = farm.area_size;
            
            const locationCell = row.insertCell();
            if (farm.location_lat && farm.location_lng) {
                locationCell.textContent = `${parseFloat(farm.location_lat).toFixed(6)}, ${parseFloat(farm.location_lng).toFixed(6)}`;
            } else {
                locationCell.textContent = 'Not set';
            }
            
            const soilTypeCell = row.insertCell();
            soilTypeCell.textContent = farm.soil_type ? farm.soil_type.name : 'Not specified';
            
            const irrigationCell = row.insertCell();
            irrigationCell.textContent = farm.irrigation_type ? 
                farm.irrigation_type.charAt(0).toUpperCase() + farm.irrigation_type.slice(1).replace('_', ' ') : 
                'None';
            
            const actionsCell = row.insertCell();
            actionsCell.innerHTML = `
                <button class="btn secondary-btn view-farm-btn" data-id="${farm.id}">View</button>
                <button class="btn text-btn edit-farm-btn" data-id="${farm.id}">Edit</button>
            `;
        });
        
        // Add event listeners to action buttons
        document.querySelectorAll('.view-farm-btn').forEach(button => {
            button.addEventListener('click', function() {
                const farmId = this.getAttribute('data-id');
                viewFarmDetails(farmId);
            });
        });
        
        document.querySelectorAll('.edit-farm-btn').forEach(button => {
            button.addEventListener('click', function() {
                const farmId = this.getAttribute('data-id');
                editFarm(farmId);
            });
        });
    }
    
    // Add farms to map
    function addFarmsToMap(farms) {
        const bounds = L.latLngBounds();
        let hasValidCoordinates = false;
        
        farms.forEach(farm => {
            if (farm.location_lat && farm.location_lng) {
                const lat = parseFloat(farm.location_lat);
                const lng = parseFloat(farm.location_lng);
                
                // Create marker
                const marker = L.marker([lat, lng])
                    .addTo(farmsMap)
                    .bindPopup(`
                        <strong>${farm.name}</strong><br>
                        Area: ${farm.area_size} acres<br>
                        <button class="popup-view-btn" data-id="${farm.id}">View Details</button>
                    `);
                
                // Event listener for popup
                marker.on('popupopen', function() {
                    document.querySelector('.popup-view-btn').addEventListener('click', function() {
                        const farmId = this.getAttribute('data-id');
                        viewFarmDetails(farmId);
                    });
                });
                
                // Add to bounds for centering the map
                bounds.extend([lat, lng]);
                hasValidCoordinates = true;
            }
            
            // Add boundary if available
            if (farm.boundary_geojson) {
                try {
                    // Parse the GeoJSON string
                    const boundaryData = JSON.parse(farm.boundary_geojson);
                    
                    // Convert GeoJSON coordinates to Leaflet format
                    if (boundaryData.type === 'Polygon' && boundaryData.coordinates && boundaryData.coordinates[0]) {
                        const coords = boundaryData.coordinates[0];
                        const latlngs = coords.map(coord => [coord[1], coord[0]]);
                        
                        const polygon = L.polygon(latlngs, {
                            color: '#3388ff',
                            fillOpacity: 0.2
                        }).addTo(farmsMap);
                        
                        // Add to bounds
                        polygon.getBounds().pad(0.1).forEach(corner => {
                            bounds.extend(corner);
                        });
                        
                        hasValidCoordinates = true;
                    }
                } catch (e) {
                    console.error('Error adding farm boundary to map:', e);
                }
            }
        });
        
        // Fit bounds if we have coordinates
        if (hasValidCoordinates) {
            farmsMap.fitBounds(bounds.pad(0.1));
        }
    }
    
    // View farm details
    function viewFarmDetails(farmId) {
        // To be implemented
        alert(`Viewing farm with ID: ${farmId}`);
    }
    
    // Edit farm
    function editFarm(farmId) {
        // To be implemented
        alert(`Editing farm with ID: ${farmId}`);
    }
    
    // Initialize with farm registration form
    showFarmRegistration();
}); 