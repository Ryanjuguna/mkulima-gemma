/**
 * Mkulima Gemma — Frontend Application Logic
 * Dynamic REST API interactions for Farm Activities, Weather Sync, Extension Services & AI Chat
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Dashboard UI components
    initChatUI();
    initActivityLoggerUI();
    initWeatherUI();
    initExtensionServicesUI();

    // Initial Data Fetching on Load
    loadActivities();
    loadWeather('Nyeri');
    loadExtensionDirectory('', '');
});

/* ==========================================
   Utility Functions & Toast Notifications
   ========================================== */

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✅' : '⚠️'}</span> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString('en-KE', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

/* Helper for resilient REST API calls trying v1 then legacy prefix */
async function apiFetch(v1Endpoint, legacyEndpoint, options = {}) {
    try {
        const res = await fetch(v1Endpoint, options);
        if (res.ok || res.status < 500) {
            return res;
        }
    } catch (e) {
        console.warn(`v1 endpoint call (${v1Endpoint}) failed, trying legacy...`, e);
    }

    if (legacyEndpoint) {
        return await fetch(legacyEndpoint, options);
    }
    throw new Error(`API fetch failed for ${v1Endpoint}`);
}

/* ==========================================
   1. AI Agronomist Chat UI
   ========================================== */

function initChatUI() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatLanguage = document.getElementById('chat-language');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const promptChips = document.querySelectorAll('.prompt-chip');

    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            const lang = chatLanguage.value;

            if (!message) return;

            chatInput.value = '';
            await sendChatMessage(message, lang);
        });
    }

    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages) {
                chatMessages.innerHTML = `
                    <div class="message bot-message">
                        <div class="message-avatar">🌱</div>
                        <div class="message-content">
                            <div class="message-header">
                                <span class="sender-name">Mkulima Gemma</span>
                                <span class="message-time">Just now</span>
                            </div>
                            <div class="message-text">Chat cleared. Ask Mkulima Gemma a question in Swahili, English, Kikuyu, or Luo!</div>
                        </div>
                    </div>
                `;
            }
        });
    }

    promptChips.forEach(chip => {
        chip.addEventListener('click', async () => {
            const prompt = chip.getAttribute('data-prompt');
            const lang = chip.getAttribute('data-lang') || 'English';

            if (chatLanguage && lang) {
                chatLanguage.value = lang;
            }

            if (prompt) {
                await sendChatMessage(prompt, chatLanguage ? chatLanguage.value : 'English');
            }
        });
    });
}

async function sendChatMessage(promptText, language) {
    const chatMessages = document.getElementById('chat-messages');
    const chatWindow = document.getElementById('chat-window');

    if (!chatMessages) return;

    // 1. Add User Message Bubble
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user-message';
    userMsgDiv.innerHTML = `
        <div class="message-avatar">🧑‍🌾</div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">You</span>
                <span class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div class="message-text">${escapeHtml(promptText)}</div>
        </div>
    `;
    chatMessages.appendChild(userMsgDiv);

    // 2. Add Thinking Bot Bubble
    const botThinkingDiv = document.createElement('div');
    botThinkingDiv.className = 'message bot-message';
    botThinkingDiv.id = 'bot-thinking-msg';
    botThinkingDiv.innerHTML = `
        <div class="message-avatar">🌱</div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">Mkulima Gemma</span>
                <span class="message-time">Analyzing...</span>
            </div>
            <div class="message-text"><i>Thinking... Consulting offline agronomy database...</i></div>
        </div>
    `;
    chatMessages.appendChild(botThinkingDiv);
    if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

    // 3. API Call to /api/chat or /api/v1/chat
    try {
        const payload = {
            message: promptText,
            language: language || 'English',
            farmer_id: 'default_farmer'
        };

        const res = await apiFetch('/api/v1/chat', '/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`Server returned HTTP ${res.status}`);
        }

        const data = await res.json();
        const aiResponse = data.response || "Sorry, I could not generate an answer at this moment.";

        // Replace thinking message with real response
        botThinkingDiv.querySelector('.message-text').innerText = aiResponse;
        botThinkingDiv.querySelector('.message-time').innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        botThinkingDiv.removeAttribute('id');

    } catch (error) {
        console.error('Chat error:', error);
        botThinkingDiv.querySelector('.message-text').innerHTML = `<span style="color: var(--danger);">Unable to connect to AI engine. Error: ${escapeHtml(error.message)}</span>`;
    }

    if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
}

/* ==========================================
   2. Activity Logger Panel
   ========================================== */

function initActivityLoggerUI() {
    const form = document.getElementById('activity-form');
    const refreshBtn = document.getElementById('refresh-activities-btn');
    const filterInput = document.getElementById('activity-crop-filter');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitActivity();
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => loadActivities());
    }

    if (filterInput) {
        filterInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            filterActivitiesTable(query);
        });
    }
}

async function loadActivities() {
    const tbody = document.getElementById('activities-tbody');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">Loading activities...</td></tr>`;

    try {
        const farmerId = document.getElementById('act-farmer-id')?.value || 'default_farmer';
        const res = await apiFetch(
            `/api/v1/activities?farmer_id=${encodeURIComponent(farmerId)}`,
            `/api/activities?farmer_id=${encodeURIComponent(farmerId)}`
        );

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const activities = data.activities || data || [];

        renderActivitiesTable(activities);

    } catch (error) {
        console.error('Error loading activities:', error);
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted" style="color: var(--danger)!important;">Failed to load activities: ${escapeHtml(error.message)}</td></tr>`;
    }
}

function renderActivitiesTable(activities) {
    const tbody = document.getElementById('activities-tbody');
    if (!tbody) return;

    if (!Array.isArray(activities) || activities.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No farm activities recorded yet. Use the form on the left to add one!</td></tr>`;
        return;
    }

    tbody.innerHTML = '';
    activities.forEach(act => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-crop', (act.crop_type || '').toLowerCase());

        const actTypeBadgeClass = act.activity_type === 'FERTILIZER_APPLICATION' ? 'badge-amber' : 
                                 act.activity_type === 'PLANTING' ? 'badge-green' : 'badge-blue';

        tr.innerHTML = `
            <td>${formatDate(act.logged_at || act.created_at)}</td>
            <td><span class="badge ${actTypeBadgeClass}">${escapeHtml(act.activity_type || 'Activity')}</span></td>
            <td><strong>${escapeHtml(act.crop_type || 'General')}</strong></td>
            <td>${escapeHtml(act.description || '-')}</td>
            <td>${act.quantity ? `${act.quantity} ${escapeHtml(act.unit || '')}` : '-'}</td>
            <td>${escapeHtml(act.field_location || 'Main Farm')}</td>
            <td>
                <button type="button" class="btn btn-danger btn-sm delete-act-btn" data-id="${act.id}">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Attach delete handlers
    document.querySelectorAll('.delete-act-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.target.getAttribute('data-id');
            if (id && confirm(`Delete activity #${id}?`)) {
                await deleteActivity(id);
            }
        });
    });
}

function filterActivitiesTable(query) {
    const rows = document.querySelectorAll('#activities-tbody tr');
    rows.forEach(row => {
        const crop = row.getAttribute('data-crop') || '';
        const text = row.innerText.toLowerCase();
        if (!query || crop.includes(query) || text.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

async function submitActivity() {
    const farmerId = document.getElementById('act-farmer-id').value || 'default_farmer';
    const activityType = document.getElementById('act-type').value;
    const cropType = document.getElementById('act-crop').value;
    const description = document.getElementById('act-desc').value;
    const quantityVal = document.getElementById('act-quantity').value;
    const unit = document.getElementById('act-unit').value;
    const fieldLocation = document.getElementById('act-field').value;
    const notes = document.getElementById('act-notes').value;

    const payload = {
        farmer_id: farmerId,
        activity_type: activityType,
        crop_type: cropType,
        description: description,
        quantity: quantityVal ? parseFloat(quantityVal) : null,
        unit: unit,
        field_location: fieldLocation,
        notes: notes
    };

    try {
        const res = await apiFetch('/api/v1/activities', '/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        showToast(`Logged activity for ${cropType}!`, 'success');
        
        // Reset crop, desc, notes inputs
        document.getElementById('act-crop').value = '';
        document.getElementById('act-desc').value = '';
        document.getElementById('act-notes').value = '';

        await loadActivities();

    } catch (error) {
        console.error('Error submitting activity:', error);
        showToast(`Failed to save activity: ${error.message}`, 'error');
    }
}

async function deleteActivity(id) {
    try {
        const res = await apiFetch(`/api/v1/activities/${id}`, `/api/activities/${id}`, {
            method: 'DELETE'
        });

        if (!res.ok && res.status !== 204) {
            throw new Error(`HTTP ${res.status}`);
        }

        showToast(`Deleted activity log #${id}`, 'success');
        await loadActivities();
    } catch (error) {
        console.error('Error deleting activity:', error);
        showToast(`Failed to delete activity: ${error.message}`, 'error');
    }
}

/* ==========================================
   3. Weather Forecast Panel
   ========================================== */

function initWeatherUI() {
    const fetchBtn = document.getElementById('fetch-weather-btn');
    const syncBtn = document.getElementById('sync-weather-btn');
    const locationInput = document.getElementById('weather-location-input');

    if (fetchBtn) {
        fetchBtn.addEventListener('click', () => {
            const loc = locationInput ? locationInput.value.trim() : 'Nyeri';
            loadWeather(loc || 'Nyeri');
        });
    }

    if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
            const loc = locationInput ? locationInput.value.trim() : 'Nyeri';
            await syncWeather(loc || 'Nyeri');
        });
    }
}

async function loadWeather(locationName) {
    const container = document.getElementById('weather-cards-container');
    if (!container) return;

    container.innerHTML = `<div class="loading-placeholder">Loading cached weather for ${escapeHtml(locationName)}...</div>`;

    try {
        const res = await apiFetch(
            `/api/v1/weather?location_name=${encodeURIComponent(locationName)}`,
            `/api/weather?location_name=${encodeURIComponent(locationName)}`
        );

        if (!res.ok) {
            if (res.status === 404) {
                container.innerHTML = `
                    <div class="loading-placeholder">
                        No cached weather found for "${escapeHtml(locationName)}". Click "Sync Weather" button to fetch initial forecast!
                    </div>
                `;
                return;
            }
            throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        const forecasts = data.cached_forecasts || data.forecasts || [];

        renderWeatherCards(forecasts, locationName);

    } catch (error) {
        console.error('Error loading weather:', error);
        container.innerHTML = `<div class="loading-placeholder" style="color: var(--danger);">Failed to load weather: ${escapeHtml(error.message)}</div>`;
    }
}

function renderWeatherCards(forecasts, locationName) {
    const container = document.getElementById('weather-cards-container');
    if (!container) return;

    if (!Array.isArray(forecasts) || forecasts.length === 0) {
        container.innerHTML = `<div class="loading-placeholder">No weather forecasts cached for ${escapeHtml(locationName)}.</div>`;
        return;
    }

    container.innerHTML = '';
    forecasts.forEach(f => {
        const card = document.createElement('div');
        card.className = 'weather-card';

        const condLower = (f.condition_text || '').toLowerCase();
        let icon = '⛅';
        if (condLower.includes('rain') || condLower.includes('shower')) icon = '🌦️';
        else if (condLower.includes('sunny') || condLower.includes('clear')) icon = '☀️';
        else if (condLower.includes('cloud')) icon = '☁️';
        else if (condLower.includes('storm')) icon = '⛈️';

        card.innerHTML = `
            <div class="w-date">${formatDate(f.forecast_date)}</div>
            <div class="w-icon">${icon}</div>
            <div class="w-temp">${f.temp_min_c ?? 14}°C - ${f.temp_max_c ?? 24}°C</div>
            <div class="w-condition">${escapeHtml(f.condition_text || 'Partly Cloudy')}</div>
            <div class="w-details">
                💧 Rain: ${f.precipitation_mm ?? 0} mm<br>
                💨 Wind: ${f.wind_speed_kmh ?? 10} km/h
            </div>
        `;
        container.appendChild(card);
    });
}

async function syncWeather(locationName) {
    try {
        showToast(`Syncing weather for ${locationName}...`, 'success');

        const payload = {
            location_name: locationName,
            latitude: -0.4167,
            longitude: 36.95
        };

        const res = await apiFetch('/api/v1/weather/sync', '/api/weather/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();
        showToast(data.message || `Successfully synced weather for ${locationName}!`, 'success');

        await loadWeather(locationName);

    } catch (error) {
        console.error('Error syncing weather:', error);
        showToast(`Weather sync failed: ${error.message}`, 'error');
    }
}

/* ==========================================
   4. Extension Services Directory Panel
   ========================================== */

function initExtensionServicesUI() {
    const searchBtn = document.getElementById('extension-search-btn');
    const searchInput = document.getElementById('extension-search-input');
    const countySelect = document.getElementById('extension-county-filter');

    const triggerSearch = () => {
        const query = searchInput ? searchInput.value.trim() : '';
        const county = countySelect ? countySelect.value : '';
        loadExtensionDirectory(query, county);
    };

    if (searchBtn) searchBtn.addEventListener('click', triggerSearch);
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') triggerSearch();
        });
    }
    if (countySelect) countySelect.addEventListener('change', triggerSearch);
}

async function loadExtensionDirectory(searchQuery = '', countyFilter = '') {
    const container = document.getElementById('extension-cards-container');
    if (!container) return;

    container.innerHTML = `<div class="loading-placeholder">Searching extension services...</div>`;

    try {
        let urlParams = new URLSearchParams();
        if (searchQuery) urlParams.append('search', searchQuery);
        if (countyFilter) urlParams.append('county', countyFilter);

        const queryString = urlParams.toString() ? `?${urlParams.toString()}` : '';

        const res = await apiFetch(
            `/api/v1/extension-services${queryString}`,
            `/api/extension-services${queryString}`
        );

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const directory = data.directory || data.services || data || [];

        renderExtensionDirectory(directory);

    } catch (error) {
        console.error('Error loading extension services:', error);
        container.innerHTML = `<div class="loading-placeholder" style="color: var(--danger);">Failed to load extension directory: ${escapeHtml(error.message)}</div>`;
    }
}

function renderExtensionDirectory(contacts) {
    const container = document.getElementById('extension-cards-container');
    if (!container) return;

    if (!Array.isArray(contacts) || contacts.length === 0) {
        container.innerHTML = `
            <div class="loading-placeholder">
                No extension service contacts found. Try adjusting your search criteria.
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    contacts.forEach(contact => {
        const card = document.createElement('div');
        card.className = 'contact-card';

        const roleText = contact.role_or_type || 'Extension Contact';
        const roleBadgeClass = roleText.includes('OFFICER') ? 'badge-green' : 'badge-blue';

        card.innerHTML = `
            <div class="contact-header">
                <div>
                    <h4>${escapeHtml(contact.name)}</h4>
                    <div class="contact-org">${escapeHtml(contact.organization || 'Ministry of Agriculture')}</div>
                </div>
                <span class="badge ${roleBadgeClass}">${escapeHtml(roleText)}</span>
            </div>
            <div class="contact-county">📍 County: <strong>${escapeHtml(contact.county_region || 'Nyeri')}</strong></div>
            <div class="contact-services">
                🌱 <strong>Services:</strong> ${escapeHtml(contact.services_offered || 'Agricultural Extension, Pest Management & Soil Advisory')}
            </div>
            <div>
                📞 <a href="tel:${escapeHtml(contact.phone_number)}" class="contact-phone">${escapeHtml(contact.phone_number || '+254 700 000000')}</a>
            </div>
            <a href="tel:${escapeHtml(contact.phone_number)}" class="btn btn-outline btn-sm btn-block" style="margin-top: 0.5rem;">📞 Call Contact</a>
        `;
        container.appendChild(card);
    });
}
