const API_BASE = "http://localhost:8000";
const USE_DEMO = true;

const demoLocations = [
    {
        id: 1,
        name: "CABS Campus Loop North",
        kind: "bus",
        capacity: 60,
        count: 20
    },
    {
        id: 2,
        name: "CABS Campus Loop South",
        kind: "bus",
        capacity: 60,
        count: 47
    },
    {
        id: 3,
        name: "COTA Campus Route",
        kind: "bus",
        capacity: 45,
        count: 17
    },
    {
        id: 4,
        name: "Traditions at Scott",
        kind: "food_court",
        capacity: 400,
        count: 340
    },
    {
        id: 5,
        name: "Traditions at Kennedy",
        kind: "food_court",
        capacity: 300,
        count: 112
    },
    {
        id: 6,
        name: "Ohio Union Dining",
        kind: "food_court",
        capacity: 250,
        count: 134
    }
];

let locations = [];
let activeFilter = "all";
let searchTerm = "";
let selectedLocationId = null;
let featuredStartIndex = 0;
let heroRotationIndex = 0;

function getPercentage(location) {
    if (!location.capacity) {
        return 0;
    }

    return Math.round((location.count / location.capacity) * 100);
}

function getLevel(percent) {
    if (percent < 40) return "low";
    if (percent < 70) return "moderate";
    if (percent < 95) return "busy";
    return "full";
}

function getLevelLabel(level) {
    const map = {
        low: "Low",
        moderate: "Moderate",
        busy: "Busy",
        full: "Full"
    };

    return map[level] || "Unknown";
}

function getTypeLabel(kind) {
    if (kind === "bus") {
        return "Campus Transportation";
    }

    return "Campus Dining";
}

function getIcon(kind) {
    if (kind === "bus") {
        return "🚌";
    }

    return "🍽️";
}

function normalizeLocation(item) {
    const occupancy = item.occupancy || {};

    return {
        id: item.id,
        name: item.name,
        kind: item.kind,
        capacity: Number(item.capacity ?? 0),
        count: Number(item.count ?? occupancy.count ?? 0)
    };
}

function buildDemoForecast(location) {
    const forecast = [];

    for (let i = 0; i < 12; i++) {
        const date = new Date();
        date.setHours(date.getHours() + i);

        const variation = Math.sin(i * 0.8) * 18 + Math.cos(i * 0.35) * 9;
        const base = getPercentage(location);
        const percentage = Math.max(8, Math.min(100, Math.round(base + variation)));

        forecast.push({
            hourLabel: date.toLocaleTimeString([], { hour: "numeric" }),
            percentage: percentage
        });
    }

    return forecast;
}

function getBestTime(forecast) {
    if (forecast.length === 0) {
        return "Unavailable";
    }

    let best = forecast[0];

    for (const point of forecast) {
        if (point.percentage < best.percentage) {
            best = point;
        }
    }

    return `${best.hourLabel} (${best.percentage}%)`;
}

async function loadLocations() {
    if (USE_DEMO) {
        locations = demoLocations.map(normalizeLocation);
    } else {
        try {
            const response = await fetch(`${API_BASE}/locations`);

            if (!response.ok) {
                throw new Error("Unable to load locations");
            }

            const data = await response.json();
            const items = Array.isArray(data) ? data : data.locations || [];
            locations = items.map(normalizeLocation);
        } catch (error) {
            console.error(error);
            locations = [];
        }
    }

    renderHeroFeature();
    renderFeaturedCarousel();
    renderLocations();
    updateStats();
    renderBestTimesList();
}

function updateStats() {
    const total = locations.length;
    const lowCount = locations.filter((location) => {
        return getLevel(getPercentage(location)) === "low";
    }).length;

    const busyCount = locations.filter((location) => {
        const level = getLevel(getPercentage(location));
        return level === "busy" || level === "full";
    }).length;

    document.getElementById("totalLocations").textContent = total;
    document.getElementById("lowCrowd").textContent = lowCount;
    document.getElementById("busyCrowd").textContent = busyCount;
    document.getElementById("lastUpdated").textContent = new Date().toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit"
    });
}

function renderHeroFeature() {
    if (locations.length === 0) {
        return;
    }

    const location = locations[heroRotationIndex % locations.length];
    const percent = getPercentage(location);
    const level = getLevel(percent);
    const forecast = buildDemoForecast(location);
    const bestTime = getBestTime(forecast);

    document.getElementById("heroFeatureName").textContent = location.name;
    document.getElementById("heroFeatureType").textContent = getTypeLabel(location.kind);
    document.getElementById("heroFeaturePeople").textContent =
        `${location.count} / ${location.capacity} people`;
    document.getElementById("heroFeaturePercent").textContent = `${percent}%`;
    document.getElementById("heroFeatureBestTime").textContent = `Best time: ${bestTime}`;

    const levelElement = document.getElementById("heroFeatureLevel");
    levelElement.textContent = getLevelLabel(level);
    levelElement.className = `status ${level}`;

    const bar = document.getElementById("heroFeatureBar");
    bar.className = `progress-fill ${level}`;
    bar.style.width = `${Math.min(percent, 100)}%`;
}

function renderFeaturedCarousel() {
    const container = document.getElementById("featuredCarousel");
    container.replaceChildren();

    if (locations.length === 0) {
        return;
    }

    const visibleItems = [];

    for (let i = 0; i < Math.min(3, locations.length); i++) {
        const index = (featuredStartIndex + i) % locations.length;
        visibleItems.push(locations[index]);
    }

    visibleItems.forEach((location) => {
        const percent = getPercentage(location);
        const level = getLevel(percent);
        const forecast = buildDemoForecast(location);
        const bestTime = getBestTime(forecast);

        const card = document.createElement("div");
        card.className = "feature-card";

        const top = document.createElement("div");
        top.className = "feature-card-top";

        const icon = document.createElement("div");
        icon.className = "feature-icon";
        icon.textContent = getIcon(location.kind);

        const status = document.createElement("span");
        status.className = `status ${level}`;
        status.textContent = getLevelLabel(level);

        top.append(icon, status);

        const title = document.createElement("h3");
        title.textContent = location.name;

        const meta = document.createElement("p");
        meta.className = "feature-meta";
        meta.textContent = `${location.count}/${location.capacity} people • ${getTypeLabel(location.kind)}`;

        const track = document.createElement("div");
        track.className = "progress-track";

        const fill = document.createElement("div");
        fill.className = `progress-fill ${level}`;
        fill.style.width = `${Math.min(percent, 100)}%`;

        track.appendChild(fill);

        const best = document.createElement("div");
        best.className = "best-time-inline";
        best.textContent = `Best time: ${bestTime}`;

        card.append(top, title, meta, track, best);

        card.addEventListener("click", () => {
            selectedLocationId = location.id;
            updateForecast(location);
            document.getElementById("insights").scrollIntoView({ behavior: "smooth" });
        });

        container.appendChild(card);
    });
}

function renderLocations() {
    const grid = document.getElementById("locationGrid");
    grid.replaceChildren();

    const filtered = locations.filter((location) => {
        const matchesFilter = activeFilter === "all" || location.kind === activeFilter;
        const matchesSearch = location.name.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
        const message = document.createElement("div");
        message.className = "empty-message";
        message.textContent = "No locations match your search.";
        grid.appendChild(message);
        return;
    }

    filtered.forEach((location) => {
        const percent = getPercentage(location);
        const level = getLevel(percent);
        const forecast = buildDemoForecast(location);
        const bestTime = getBestTime(forecast);

        const card = document.createElement("article");
        card.className = "location-card";

        const top = document.createElement("div");
        top.className = "card-top";

        const icon = document.createElement("span");
        icon.className = "location-icon";
        icon.textContent = getIcon(location.kind);

        const status = document.createElement("span");
        status.className = `status ${level}`;
        status.textContent = getLevelLabel(level);

        top.append(icon, status);

        const title = document.createElement("h3");
        title.textContent = location.name;

        const type = document.createElement("p");
        type.className = "location-type";
        type.textContent = getTypeLabel(location.kind);

        const occupancy = document.createElement("div");
        occupancy.className = "occupancy-label";

        const people = document.createElement("span");
        people.textContent = `${location.count} / ${location.capacity} people`;

        const percentText = document.createElement("strong");
        percentText.textContent = `${percent}%`;

        occupancy.append(people, percentText);

        const track = document.createElement("div");
        track.className = "progress-track";

        const fill = document.createElement("div");
        fill.className = `progress-fill ${level}`;
        fill.style.width = `${Math.min(percent, 100)}%`;

        track.appendChild(fill);

        const bottom = document.createElement("div");
        bottom.className = "card-bottom";

        const info = document.createElement("small");
        info.innerHTML = `Current crowd: <strong>${getLevelLabel(level)}</strong><br>Best time: <strong>${bestTime}</strong>`;

        const button = document.createElement("button");
        button.className = "view-button";
        button.textContent = "View Forecast →";
        button.addEventListener("click", () => {
            selectedLocationId = location.id;
            updateForecast(location);
            document.getElementById("insights").scrollIntoView({ behavior: "smooth" });
        });

        bottom.append(info, button);

        card.append(top, title, type, occupancy, track, bottom);
        grid.appendChild(card);
    });
}

function renderBestTimesList() {
    const list = document.getElementById("bestTimesList");
    list.replaceChildren();

    locations.forEach((location) => {
        const forecast = buildDemoForecast(location);
        const bestTime = getBestTime(forecast);
        const percent = getPercentage(location);
        const level = getLevel(percent);

        const item = document.createElement("div");
        item.className = "best-time-card";

        const top = document.createElement("div");
        top.className = "best-time-card-top";

        const left = document.createElement("div");

        const title = document.createElement("h4");
        title.textContent = location.name;

        const text = document.createElement("p");
        text.textContent = `${getTypeLabel(location.kind)} • Current: ${getLevelLabel(level)}`;

        left.append(title, text);

        const badge = document.createElement("span");
        badge.className = `status ${level}`;
        badge.textContent = bestTime;

        top.append(left, badge);
        item.appendChild(top);

        item.addEventListener("click", () => {
            selectedLocationId = location.id;
            updateForecast(location);
        });

        list.appendChild(item);
    });
}

function updateForecast(location) {
    const title = document.getElementById("forecastTitle");
    const subtitle = document.getElementById("forecastSubtitle");
    const chart = document.getElementById("forecastChart");

    title.textContent = location.name;
    chart.replaceChildren();

    const forecast = buildDemoForecast(location);
    const bestTime = getBestTime(forecast);

    subtitle.textContent = `Best time to go: ${bestTime}`;

    forecast.forEach((point) => {
        const col = document.createElement("div");
        col.className = "forecast-column";

        const value = document.createElement("strong");
        value.textContent = `${point.percentage}%`;

        const track = document.createElement("div");
        track.className = "forecast-bar-track";

        const bar = document.createElement("div");
        bar.className = "forecast-bar";
        bar.style.height = `${point.percentage}%`;

        track.appendChild(bar);

        const hour = document.createElement("small");
        hour.textContent = point.hourLabel;

        col.append(value, track, hour);
        chart.appendChild(col);
    });
}

function setupFilters() {
    const filterButtons = document.querySelectorAll(".filter");

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            filterButtons.forEach((item) => {
                item.classList.remove("active");
            });

            button.classList.add("active");
            activeFilter = button.dataset.kind;
            renderLocations();
        });
    });

    document.getElementById("searchInput").addEventListener("input", (event) => {
        searchTerm = event.target.value;
        renderLocations();
    });
}

function setupCarouselButtons() {
    document.getElementById("prevFeature").addEventListener("click", () => {
        if (locations.length === 0) return;
        featuredStartIndex = (featuredStartIndex - 1 + locations.length) % locations.length;
        renderFeaturedCarousel();
    });

    document.getElementById("nextFeature").addEventListener("click", () => {
        if (locations.length === 0) return;
        featuredStartIndex = (featuredStartIndex + 1) % locations.length;
        renderFeaturedCarousel();
    });
}

function autoRotateHero() {
    setInterval(() => {
        if (locations.length === 0) return;
        heroRotationIndex = (heroRotationIndex + 1) % locations.length;
        renderHeroFeature();
    }, 3500);
}

function autoRotateFeatured() {
    setInterval(() => {
        if (locations.length === 0) return;
        featuredStartIndex = (featuredStartIndex + 1) % locations.length;
        renderFeaturedCarousel();
    }, 5000);
}

setupFilters();
setupCarouselButtons();
loadLocations();
autoRotateHero();
autoRotateFeatured();