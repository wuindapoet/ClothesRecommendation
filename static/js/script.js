let map;
let marker;
let selectedLocation = null;

/* Map Initialization */
function initMap() {
    const defaultCenter = [10.7962516, 106.7223281]; // Landmark 81

    map = L.map('map').setView(defaultCenter, 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    map.on('click', e => placeMarker(e.latlng));
}

/* Place Marker */
function placeMarker(latlng) {
    if (marker) map.removeLayer(marker);

    marker = L.marker(latlng).addTo(map);

    selectedLocation = {
        lat: latlng.lat,
        lng: latlng.lng
    };

    document.getElementById('locationInfo').style.display = 'block';
    document.getElementById('latLng').textContent =
        `Latitude: ${latlng.lat.toFixed(6)}, Longitude: ${latlng.lng.toFixed(6)}`;

    updateSubmitButton();
}

/* Update Submit Button */
function updateSubmitButton() {
    const gender = document.getElementById('genderSelect').value;
    const age = parseInt(document.getElementById('ageInput').value);
    const occasion = document.getElementById('occasionSelect').value;
    const k = parseInt(document.getElementById('kInput').value);

    const submitBtn = document.getElementById('submitBtn');

    const validAge = age >= 15 && age <= 50;
    const validK = k >= 1 && k <= 10;

    const ageError = document.getElementById('ageError');
    if (ageError) {
        if (age && !validAge) {
            ageError.textContent = "Age must be between 15 and 50";
        } else {
            ageError.textContent = "";
        }
    }

    const dateValue = document.getElementById("dateInput").value;
    let validDate = false;

    if (dateValue) {
        const selected = new Date(dateValue);
        const today = new Date();
        const max = new Date();
        max.setDate(today.getDate() + 15);

        validDate = selected >= today && selected <= max;
    }

    submitBtn.disabled = !(gender && occasion && selectedLocation && validAge && validK && validDate);
}

/* Input Listeners */
['genderSelect', 'ageInput', 'occasionSelect', 'kInput', 'dateInput'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('input', updateSubmitButton);
    }
});

/* Location Search */
let searchTimeout;
const searchInput = document.getElementById('locationSearch');
const searchResults = document.getElementById('searchResults');

if (searchInput && searchResults) {
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        clearTimeout(searchTimeout);

        if (query.length < 3) {
            searchResults.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const res = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
                    { headers: { 'User-Agent': 'LocationPickerApp/1.0' } }
                );

                const data = await res.json();
                renderSearchResults(data);
            } catch {
                searchResults.innerHTML =
                    '<div class="search-result-item">Search error</div>';
                searchResults.style.display = 'block';
            }
        }, 500);
    });
}

function renderSearchResults(results) {
    searchResults.innerHTML = '';

    if (!results.length) {
        searchResults.innerHTML =
            '<div class="search-result-item">No results found</div>';
        searchResults.style.display = 'block';
        return;
    }

    results.forEach(item => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        div.innerHTML = `
            <strong>${item.display_name.split(',')[0]}</strong>
            <span>${item.display_name}</span>
        `;

        div.onclick = () => {
            const latlng = {
                lat: parseFloat(item.lat),
                lng: parseFloat(item.lon)
            };
            map.setView([latlng.lat, latlng.lng], 15);
            placeMarker(latlng);
            searchInput.value = item.display_name;
            searchResults.style.display = 'none';
        };

        searchResults.appendChild(div);
    });

    searchResults.style.display = 'block';
}

document.addEventListener('click', e => {
    if (!searchInput || !searchResults) return;
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
    }
});

/* Submit */
const submitBtn = document.getElementById('submitBtn');
if (submitBtn) {
    submitBtn.addEventListener('click', async () => {
        const data = {
            gender: document.getElementById('genderSelect').value,
            age: parseInt(document.getElementById('ageInput').value),
            occasion: document.getElementById('occasionSelect').value,
            k: parseInt(document.getElementById('kInput').value),
            date: document.getElementById('dateInput').value,
            location: selectedLocation
        };

        const statusMsg = document.getElementById('statusMsg');

        try {
            submitBtn.disabled = true;
            statusMsg.style.display = 'none';

            const res = await fetch('/process-location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await res.json();
            if (!res.ok) throw new Error(result.error || 'Submission failed');

            statusMsg.className = 'status success';
            statusMsg.textContent = result.message || 'Success!';
            statusMsg.style.display = 'block';

            renderResult(result.data?.result || []);
        } catch (err) {
            statusMsg.className = 'status error';
            statusMsg.textContent = err.message;
            statusMsg.style.display = 'block';
            submitBtn.disabled = false;
        }
    });
}

/* Render Result */
function renderResult(list) {
    if (!Array.isArray(list)) return;

    const box = document.getElementById('resultBox');
    const grid = document.getElementById('resultList');
    grid.innerHTML = '';

    list.forEach(item => {
        const score = Math.round(item.score * 100);
        const card = document.createElement('div');
        card.className = 'reco-card';

        // Internet search links (Shopee/Google)
        const links = item.buy_links || {};
        let buyBtns = '';
        if (links && (links.shopee || links.google || links.google_shopping || links.google_images)) {
            buyBtns += '<div class="buy-links">';
            if (links.shopee) buyBtns += `<a class="buy-btn" href="${links.shopee}" target="_blank" rel="noopener">Shopee</a>`;
            if (links.google) buyBtns += `<a class="buy-btn" href="${links.google}" target="_blank" rel="noopener">Google</a>`;
            if (links.google_shopping) buyBtns += `<a class="buy-btn" href="${links.google_shopping}" target="_blank" rel="noopener">Google Shopping</a>`;
            if (links.google_images) buyBtns += `<a class="buy-btn" href="${links.google_images}" target="_blank" rel="noopener">Google Images</a>`;
            buyBtns += '</div>';
        }
        card.innerHTML = `
            <img src="${item.image}" onerror="this.src='/static/images/placeholder.jpg'">
            <div class="reco-content">
                <div class="reco-title">${item.type}</div>
                <div class="reco-sub">${item.usage} · ${item.season}</div>
                <div class="score-label">Match ${score}%</div>
                <div class="score-bar">
                    <div class="score-fill" style="width:${score}%"></div>
                </div>
                <div class="reason">✔ ${item.usage}</div>
                <div class="reason">✔ ${item.season}</div>
                ${buyBtns}
            </div>
        `;
        grid.appendChild(card);
    });

    box.style.display = 'block';
}

/* Start Map */
window.addEventListener('DOMContentLoaded', () => {
    const mapEl = document.getElementById("map");
    if (mapEl && typeof L !== "undefined") {
        initMap();
    }
});

/* Feedback Handling */
document.addEventListener("DOMContentLoaded", () => {
    const feedbackBtn = document.getElementById("feedbackBtn");
    console.log("feedbackBtn =", feedbackBtn);

    if (!feedbackBtn) return;

    feedbackBtn.addEventListener("click", async () => {
        console.log("FEEDBACK BUTTON CLICKED");
        const rating = document.querySelector('input[name="rating"]:checked')?.value;
        const feedback = document.getElementById("feedbackText").value.trim();
        const status = document.getElementById("feedbackStatus");

        status.style.display = "none";

        if (!rating || !feedback) {
            status.textContent = "Please select a rating and write feedback.";
            status.style.display = "block";
            return;
        }

        try {
            const res = await fetch("/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rating, feedback })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "Server error");
            }

            status.textContent = "Thank you for your feedback 💜";
            status.style.display = "block";

            document.querySelectorAll('input[name="rating"]').forEach(r => r.checked = false);
            document.getElementById("feedbackText").value = "";

            setTimeout(() => {
                window.location.reload();
            }, 10000);

        } catch (err) {
            status.textContent = err.message;
            status.style.display = "block";
        }
    });
});

/* Date Input Constraints */
document.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("dateInput");
    if (!dateInput) return;

    const today = new Date();
    const maxDate = new Date();
    maxDate.setDate(today.getDate() + 15);

    dateInput.min = today.toISOString().split("T")[0];
    dateInput.max = maxDate.toISOString().split("T")[0];
});


function getSelectedRating() {
    const checked = document.querySelector('input[name="rating"]:checked');
    return checked ? parseInt(checked.value) : 0;
}