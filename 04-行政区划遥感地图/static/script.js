/**
 * 中国行政区划 + 遥感研究数据地图
 * China Administrative Divisions + Remote Sensing Map - Frontend Logic
 *
 * 三级视图：
 *   1. national  - 全国视图：显示 34 个省份标记 + 遥感数据点
 *   2. province  - 省份视图：放大显示某省，标记所有下辖城市
 *   3. city      - 城市视图：聚焦于某城市，弹出详细信息
 */

// ==================== 全局状态 ====================
let map = null;
let provinceLayer = null;      // 全国视图：省份标记层
let cityLayer = null;          // 省份视图：城市标记层
let districtLayer = null;      // 区县视图：区县标记层（聚类）
let researchLayer = null;      // 遥感研究点聚合层
let showProvinces = true;
let showResearch = true;

let mapState = {
    mode: 'national',          // national | province | city
    currentProvinceName: null,
    currentCityId: null,
    currentCityLat: null,
    currentCityLng: null,
    provincesData: [],
    citiesByProvince: {},      // 缓存：省份 -> 城市数组

    // === 缩放自适应模式 ===
    displayMode: 'auto',       // 'auto' | 'focused'
    focusedLevel: null,        // null | 'province' | 'city'
    autoLevel: 'province',     // 当前缩放自动检测的层级
    allCitiesData: [],         // 全部343个城市数据
    districtsByCity: {},       // 缓存：cityId -> district[]

    // === 防抖和状态跟踪 ===
    previousZoom: 5,
    zoomHandlerTimer: null,
    boundsLoadTimer: null,
    boundsRequestId: 0,
    isTransitioning: false
};

const CHINA_CENTER = [35.5, 104.0];
const CHINA_ZOOM = 5;

// ==================== 地图初始化 ====================

function initMap() {
    map = L.map('map', {
        center: CHINA_CENTER,
        zoom: CHINA_ZOOM,
        minZoom: 4,
        maxZoom: 16,
        maxBounds: [[0, 70], [55, 140]],
        maxBoundsViscosity: 0.6,
        zoomControl: true
    });

    // 高德卫星
    const gaodeSat = L.tileLayer(
        'https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
        { subdomains: ['1', '2', '3', '4'], attribution: '© 高德地图', maxZoom: 18 }
    );

    // 高德标准（道路+地名）
    const gaodeNormal = L.tileLayer(
        'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
        { subdomains: ['1', '2', '3', '4'], attribution: '© 高德地图', maxZoom: 18 }
    );

    // 高德卫星+路网
    const gaodeHybrid = L.layerGroup([
        L.tileLayer('https://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            { subdomains: ['1', '2', '3', '4'], maxZoom: 18 }),
        L.tileLayer('https://webst0{s}.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}',
            { subdomains: ['1', '2', '3', '4'], maxZoom: 18 })
    ]);

    // OSM
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        { attribution: '© OpenStreetMap', maxZoom: 18 });

    // 默认：高德标准
    gaodeNormal.addTo(map);

    L.control.layers({
        '高德地图': gaodeNormal,
        '高德卫星图': gaodeSat,
        '高德卫星+路网': gaodeHybrid,
        'OpenStreetMap': osm
    }, null, { position: 'topright' }).addTo(map);

    L.control.scale({ metric: true, imperial: false, position: 'bottomleft' }).addTo(map);

    // 地图空白区域点击：关闭所有弹窗
    map.on('click', function(e) {
        // 只在点击到地图本身（非标记）时关闭
        if (!e.originalEvent.target.closest('.leaflet-marker-icon') &&
            !e.originalEvent.target.closest('.leaflet-popup') &&
            !e.originalEvent.target.closest('.leaflet-tooltip') &&
            !e.originalEvent.target.closest('.leaflet-control')) {
            map.closePopup();
        }
    });

    // 初始化各图层组
    provinceLayer = L.layerGroup().addTo(map);
    cityLayer = L.layerGroup().addTo(map);
    researchLayer = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 55,
        showCoverageOnHover: false,
        iconCreateFunction: function (cluster) {
            const count = cluster.getChildCount();
            let cls = 'cluster-small';
            if (count >= 20) cls = 'cluster-large';
            else if (count >= 10) cls = 'cluster-medium';
            return L.divIcon({
                html: '<div class="cluster-icon ' + cls + '"><span>' + count + '</span></div>',
                className: 'custom-cluster',
                iconSize: L.point(40, 40)
            });
        }
    });
    map.addLayer(researchLayer);

    // 区县聚合层
    districtLayer = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 40,
        showCoverageOnHover: false,
        iconCreateFunction: function (cluster) {
            const count = cluster.getChildCount();
            let cls = 'district-cluster-small';
            if (count >= 15) cls = 'district-cluster-large';
            else if (count >= 8) cls = 'district-cluster-medium';
            return L.divIcon({
                html: '<div class="cluster-icon ' + cls + '"><span>' + count + '</span></div>',
                className: 'custom-cluster',
                iconSize: L.point(34, 34)
            });
        }
    });
    map.addLayer(districtLayer);
}

// ==================== 自定义图标 ====================

function createProvinceIcon(provinceName, abbreviation) {
    return L.divIcon({
        html: `<div class="province-marker">
                  <div class="province-marker-pin">${abbreviation || '?'}</div>
                  <div class="province-marker-name">${provinceName}</div>
               </div>`,
        className: 'province-marker-container',
        iconSize: L.point(70, 50),
        iconAnchor: [35, 50]
    });
}

function createCityIcon(city) {
    const level = city.level || '';
    let color = '#3498db';   // 默认地级市蓝
    let symbol = '●';
    let size = 26;

    if (level.includes('省会') || level === '直辖市' || level === '副省级') {
        color = '#f39c12';   // 省会橙
        symbol = '★';
        size = 32;
    } else if (level.includes('自治州') || level === '盟' || level === '地区') {
        color = '#9b59b6';   // 自治州紫
        symbol = '◆';
        size = 28;
    } else if (level === '特别行政区') {
        color = '#e91e63';
        symbol = '✦';
        size = 30;
    }

    return L.divIcon({
        html: `<div class="city-marker" style="background:${color};width:${size}px;height:${size}px;font-size:${size * 0.5}px;">
                  ${symbol}
                  <span class="city-marker-label">${city.name}</span>
               </div>`,
        className: 'city-marker-container',
        iconSize: L.point(size, size),
        iconAnchor: [size / 2, size / 2]
    });
}

function createResearchIcon() {
    return L.divIcon({
        html: '<div class="research-marker">🛰️</div>',
        className: 'research-marker-container',
        iconSize: L.point(24, 24),
        iconAnchor: [12, 12]
    });
}

function createDistrictIcon(district) {
    const type = district.type || '市辖区';
    let color = '#2ecc71';   // 市辖区: green
    let symbol = '■';
    let size = 20;

    if (type === '县级市') {
        color = '#1abc9c';   // teal
        symbol = '◆';
        size = 22;
    } else if (type === '县' || type === '自治县') {
        color = '#95a5a6';   // gray
        symbol = '●';
        size = 18;
    } else if (type === '旗' || type === '自治旗') {
        color = '#8e44ad';   // purple
        symbol = '▲';
        size = 18;
    }

    return L.divIcon({
        html: `<div class="district-marker" style="background:${color};width:${size}px;height:${size}px;font-size:${size * 0.45}px;">
                  ${symbol}
                  <span class="district-marker-label">${district.name}</span>
               </div>`,
        className: 'district-marker-container',
        iconSize: L.point(size, size + 16),
        iconAnchor: [size / 2, size / 2]
    });
}

function renderDistrictMarkers(districts) {
    districtLayer.clearLayers();
    if (!districts || districts.length === 0) return;

    districts.forEach(d => {
        const marker = L.marker([d.latitude, d.longitude], {
            icon: createDistrictIcon(d)
        });

        marker.bindTooltip(
            `<strong>${d.name}</strong> · ${d.type || '区县'}<br/>
             ${d.city_name} · 人口：${d.population || '-'} 万`,
            { direction: 'top', className: 'custom-tooltip' }
        );

        marker.on('click', async () => {
            await enterDistrict(d.id, d.latitude, d.longitude);
        });

        districtLayer.addLayer(marker);
    });
}

// ==================== 数据加载 ====================

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
}

async function loadProvinces() {
    try {
        const provinces = await fetchJSON('/api/provinces');
        mapState.provincesData = provinces;
        return provinces;
    } catch (e) {
        console.error('加载省份失败：', e);
        showError('加载省份数据失败');
        return [];
    }
}

async function loadCitiesByProvince(province) {
    if (mapState.citiesByProvince[province]) {
        return mapState.citiesByProvince[province];
    }
    try {
        const cities = await fetchJSON('/api/cities?province=' + encodeURIComponent(province));
        mapState.citiesByProvince[province] = cities;
        return cities;
    } catch (e) {
        console.error('加载城市失败：', e);
        return [];
    }
}

async function loadCityDetail(cityId) {
    try {
        return await fetchJSON('/api/city/' + cityId);
    } catch (e) {
        console.error('加载城市详情失败：', e);
        return null;
    }
}

async function loadProvinceDetail(provinceName) {
    try {
        return await fetchJSON('/api/province/' + encodeURIComponent(provinceName));
    } catch (e) {
        console.error('加载省份详情失败：', e);
        return null;
    }
}

async function loadResearchPoints(province) {
    let url = '/api/points';
    if (province) url += '?province=' + encodeURIComponent(province);
    try {
        return await fetchJSON(url);
    } catch (e) {
        console.error('加载遥感数据失败：', e);
        return [];
    }
}

async function loadStats() {
    try {
        return await fetchJSON('/api/stats');
    } catch (e) {
        console.error('加载统计失败：', e);
        return null;
    }
}

// ==================== 状态指示器 ====================

function setLoading(panelId, isLoading) {
    const panels = {
        'panelProvince': 'loaderProvince',
        'panelCity': 'loaderCity'
    };
    const el = document.getElementById(panelId);
    if (!el) return;
    if (isLoading) {
        el.classList.add('panel-loading');
        // 显示对应的 loader
        const loaderId = panels[panelId];
        if (loaderId) {
            const loader = document.getElementById(loaderId);
            if (loader) loader.style.display = 'flex';
        }
    } else {
        el.classList.remove('panel-loading');
        // 隐藏对应的 loader
        const loaderId = panels[panelId];
        if (loaderId) {
            const loader = document.getElementById(loaderId);
            if (loader) loader.style.display = 'none';
        }
    }
}

// ==================== 渲染：全国视图 ====================

function renderProvinceMarkers(provinces) {
    provinceLayer.clearLayers();
    if (!showProvinces) return;

    provinces.forEach(p => {
        const province = mapState.provincesData.find(x => x.name === p.name) || p;
        const capitalCity = findCapitalCoords(province);
        if (!capitalCity) return;

        const icon = createProvinceIcon(province.name, province.abbreviation);
        const marker = L.marker([capitalCity.lat, capitalCity.lng], { icon: icon });

        marker.bindTooltip(
            `<strong>${province.name}</strong><br/>
             省会：${province.capital}<br/>
             城市数：${province.city_count}<br/>
             点击查看详情`,
            { direction: 'top', className: 'custom-tooltip' }
        );

        marker.on('click', () => {
            enterProvince(province.name);
        });

        provinceLayer.addLayer(marker);
    });
}

// 已知省会经纬度（用于全国视图省份标记定位）
const PROVINCE_CENTER = {
    '北京市': [39.9042, 116.4074], '天津市': [39.1330, 117.2008], '上海市': [31.2304, 121.4737],
    '重庆市': [29.5630, 106.5516], '河北省': [38.0428, 114.5149], '山西省': [37.8706, 112.5489],
    '内蒙古自治区': [40.8423, 111.7491], '辽宁省': [41.8057, 123.4315], '吉林省': [43.8868, 125.3245],
    '黑龙江省': [45.8023, 126.5358], '江苏省': [32.0603, 118.7969], '浙江省': [30.2741, 120.1551],
    '安徽省': [31.8206, 117.2272], '福建省': [26.0745, 119.2965], '江西省': [28.6820, 115.8579],
    '山东省': [36.6758, 117.0009], '河南省': [34.7466, 113.6253], '湖北省': [30.5928, 114.3055],
    '湖南省': [28.2278, 112.9388], '广东省': [23.1291, 113.2644], '广西壮族自治区': [22.8170, 108.3669],
    '海南省': [20.0312, 110.3312], '四川省': [30.5728, 104.0668], '贵州省': [26.6470, 106.6302],
    '云南省': [25.0406, 102.7123], '西藏自治区': [29.6604, 91.1322], '陕西省': [34.3416, 108.9398],
    '甘肃省': [36.0611, 103.8343], '青海省': [36.6232, 101.7782], '宁夏回族自治区': [38.4872, 106.2306],
    '新疆维吾尔自治区': [43.8256, 87.6168], '台湾省': [25.0330, 121.5654],
    '香港特别行政区': [22.3193, 114.1694], '澳门特别行政区': [22.1987, 113.5439]
};

function findCapitalCoords(province) {
    const c = PROVINCE_CENTER[province.name];
    if (c) return { lat: c[0], lng: c[1] };
    return null;
}

function renderResearchPoints(points) {
    researchLayer.clearLayers();
    if (!showResearch) return;

    points.forEach(p => {
        const marker = L.marker([p.latitude, p.longitude], { icon: createResearchIcon() });

        const yearBadge = p.year ? `<span class="popup-badge popup-year">📅 ${p.year}</span>` : '';
        const provinceBadge = p.province ? `<span class="popup-badge popup-province">📍 ${p.province}</span>` : '';

        // 地图上的快速弹出气泡（摘要）
        marker.bindPopup(`
            <div class="popup-content">
                <div class="popup-header popup-research-header">
                    <h3>${p.title || '遥感研究数据点'}</h3>
                    <div class="popup-badges">${yearBadge}${provinceBadge}</div>
                </div>
                <div class="popup-body">
                    <div class="popup-field"><span class="popup-label">👤 作者：</span><span>${p.author}</span></div>
                    <div class="popup-field"><span class="popup-label">🏛️ 单位：</span><span>${p.institution}</span></div>
                    <div class="popup-field popup-overview">
                        <span class="popup-label">📝 研究概述：</span>
                        <p>${p.overview}</p>
                    </div>
                    <div style="text-align:center;margin-top:10px;">
                        <span style="color:#e74c3c;font-size:0.78rem;cursor:pointer;"
                              onclick="event.preventDefault();document.querySelector('.leaflet-popup-close-button').click();">
                          💡 点击标记查看详细分类卡片 →
                        </span>
                    </div>
                </div>
            </div>
        `, { maxWidth: 380, className: 'custom-popup' });

        // 点击标记 → 打开侧边栏详细卡片
        marker.on('click', async () => {
            map.closePopup();
            await showResearchDetailCard(p);
        });

        marker.bindTooltip(p.title || p.overview.substring(0, 25), {
            direction: 'top', className: 'custom-tooltip'
        });

        researchLayer.addLayer(marker);
    });
}

// ==================== 渲染：省份视图 ====================

function renderCityMarkers(cities) {
    cityLayer.clearLayers();

    cities.forEach(city => {
        const marker = L.marker([city.latitude, city.longitude], {
            icon: createCityIcon(city)
        });

        marker.bindTooltip(
            `<strong>${city.name}</strong> · ${city.level || '地级市'}<br/>
             人口：${city.population || '-'} 万 · GDP：${city.gdp || '-'} 亿`,
            { direction: 'top', className: 'custom-tooltip' }
        );

        marker.on('click', () => {
            enterCity(city.id, city.latitude, city.longitude);
        });

        cityLayer.addLayer(marker);
    });
}

// ==================== 模式切换 ====================

async function enterNational() {
    mapState.mode = 'national';
    mapState.currentProvinceName = null;
    mapState.currentCityId = null;
    mapState.currentCityLat = null;
    mapState.currentCityLng = null;

    // 切换到自动模式
    mapState.displayMode = 'auto';
    mapState.focusedLevel = null;

    // 清除城市层和区县层
    cityLayer.clearLayers();
    districtLayer.clearLayers();

    // 恢复全国视图
    map.flyTo(CHINA_CENTER, CHINA_ZOOM, { duration: 1.2 });

    // 渲染省份标记
    renderProvinceMarkers(mapState.provincesData);

    // 加载全国遥感数据
    const points = await loadResearchPoints();
    renderResearchPoints(points);

    // 更新自动级别
    mapState.autoLevel = 'province';
    mapState.previousZoom = CHINA_ZOOM;

    // 更新 UI
    showPanel('panelNational');
    updateBreadcrumb('national');
    updateModeHint('💡 全国省份 · 滚动放大查看地级市，继续放大查看区县');
}

async function enterProvince(provinceName) {
    mapState.mode = 'province';
    mapState.currentProvinceName = provinceName;
    mapState.currentCityId = null;
    mapState.currentCityLat = null;
    mapState.currentCityLng = null;

    // 切换到聚焦模式
    mapState.displayMode = 'focused';
    mapState.focusedLevel = 'province';

    // 清除省份标记和遥感点、区县
    provinceLayer.clearLayers();
    researchLayer.clearLayers();
    cityLayer.clearLayers();
    districtLayer.clearLayers();

    // 显示加载状态
    setLoading('panelProvince', true);
    showPanel('panelProvince');

    // 加载省份详情 + 城市列表
    const detail = await loadProvinceDetail(provinceName);
    if (!detail) {
        showError('加载省份详情失败');
        setLoading('panelProvince', false);
        return;
    }

    // 渲染城市标记
    renderCityMarkers(detail.cities);

    // 计算地图视野并飞行
    if (detail.cities.length > 0) {
        const bounds = L.latLngBounds(detail.cities.map(c => [c.latitude, c.longitude]));
        map.flyToBounds(bounds, { padding: [60, 60], maxZoom: 9, duration: 1.5 });
    } else {
        const center = PROVINCE_CENTER[provinceName];
        if (center) map.flyTo(center, 8, { duration: 1.5 });
    }

    // 加载该省份的遥感研究点
    if (showResearch) {
        const points = await loadResearchPoints(provinceName);
        renderResearchPoints(points);
    }

    // 填充省份信息面板
    fillProvincePanel(detail);
    setLoading('panelProvince', false);
    showPanel('panelProvince');
    updateBreadcrumb('province', provinceName);
    updateModeHint(`💡 当前显示：${provinceName} · 点击城市标记查看详情 · 放大查看区县`);
}

async function enterCity(cityId, lat, lng) {
    // 如果是首次进入城市（从搜索直接跳转，省份可能未加载城市标记）
    // 确保 cityLayer 有内容
    if (mapState.mode === 'national' || mapState.mode === 'province') {
        // 如果当前省份视图没有渲染城市标记，需要先渲染
        const provinceName = mapState.currentProvinceName;
        if (provinceName && cityLayer.getLayers().length === 0) {
            const cities = await loadCitiesByProvince(provinceName);
            if (cities.length > 0) {
                renderCityMarkers(cities);
            }
        }
    }

    mapState.mode = 'city';
    mapState.currentCityId = cityId;
    mapState.currentCityLat = lat;
    mapState.currentCityLng = lng;

    // 切换到聚焦模式
    mapState.displayMode = 'focused';
    mapState.focusedLevel = 'city';

    // 飞行到城市
    map.flyTo([lat, lng], 11, { duration: 1.0 });

    // 显示加载状态
    setLoading('panelCity', true);
    showPanel('panelCity');

    // 加载城市详情
    const detail = await loadCityDetail(cityId);
    if (!detail) {
        showError('加载城市详情失败');
        setLoading('panelCity', false);
        return;
    }

    fillCityPanel(detail);
    setLoading('panelCity', false);
    showPanel('panelCity');
    updateBreadcrumb('city', mapState.currentProvinceName || detail.province, detail.name);
    updateModeHint(`💡 当前显示：${detail.name} 详情 · 查看左侧城市介绍、文化底蕴和景点`);

    // 弹出城市信息气泡
    showCityPopup(detail, lat, lng);
}

function showCityPopup(detail, lat, lng) {
    // 先关闭已有弹出框
    map.closePopup();

    const popupHtml = `
        <div class="popup-content">
            <div class="popup-header popup-city-header">
                <h3>${detail.name}</h3>
                <div class="popup-badges">
                    <span class="popup-badge">📍 ${detail.province}</span>
                    <span class="popup-badge">🏛️ ${detail.level}</span>
                </div>
            </div>
            <div class="popup-body">
                <div class="popup-field"><span class="popup-label">人口：</span>${detail.population || '-'} 万</div>
                <div class="popup-field"><span class="popup-label">GDP：</span>${detail.gdp || '-'} 亿元</div>
                <div class="popup-field"><span class="popup-label">面积：</span>${detail.area || '-'} km²</div>
                <div class="popup-field popup-overview">
                    <span class="popup-label">📖 介绍：</span>
                    <p>${detail.intro || '-'}</p>
                </div>
            </div>
        </div>
    `;
    L.popup({ maxWidth: 380, className: 'custom-popup' })
        .setLatLng([lat, lng])
        .setContent(popupHtml)
        .openOn(map);
}

// ==================== 缩放自适应模式 ====================

const ZOOM_THRESHOLDS = {
    PROVINCE:  { min: 4, max: 6 },
    CITY:      { min: 7, max: 9 },
    DISTRICT:  { min: 10, max: 12 },
    DETAIL:    { min: 13, max: 16 }
};

function getLevelFromZoom(zoom) {
    const z = Math.round(zoom);
    if (z >= 4 && z <= 6) return 'province';
    if (z >= 7 && z <= 9) return 'city';
    if (z >= 10 && z <= 12) return 'district';
    return 'detail';
}

function setupZoomHandler() {
    map.on('zoomend', function() {
        clearTimeout(mapState.zoomHandlerTimer);
        mapState.zoomHandlerTimer = setTimeout(() => {
            const newZoom = Math.round(map.getZoom());
            const oldZoom = mapState.previousZoom;
            mapState.previousZoom = newZoom;

            if (mapState.isTransitioning) return;

            if (mapState.displayMode === 'auto') {
                handleAutoZoomChange(newZoom, oldZoom);
            } else {
                handleFocusedZoomChange(newZoom);
            }
        }, 200);
    });

    // 在city和district层级平移时刷新内容
    map.on('moveend', function() {
        if (mapState.isTransitioning) return;
        if (mapState.displayMode === 'auto' &&
            (mapState.autoLevel === 'city' || mapState.autoLevel === 'district')) {
            clearTimeout(mapState.boundsLoadTimer);
            mapState.boundsLoadTimer = setTimeout(() => {
                refreshBoundsContent();
            }, 300);
        }
    });
}

function handleAutoZoomChange(newZoom, oldZoom) {
    const newLevel = getLevelFromZoom(newZoom);
    const oldLevel = getLevelFromZoom(oldZoom);
    if (newLevel === oldLevel) return;

    mapState.isTransitioning = true;
    mapState.autoLevel = newLevel;

    switch (newLevel) {
        case 'province':
            // 省份标记
            cityLayer.clearLayers();
            districtLayer.clearLayers();
            if (showProvinces) {
                renderProvinceMarkers(mapState.provincesData);
            }
            showPanel('panelNational');
            updateBreadcrumb('national');
            updateModeHint('💡 全国省份 · 滚动放大查看地级市');
            break;

        case 'city':
            // 城市标记 — 显示视口内的城市
            provinceLayer.clearLayers();
            districtLayer.clearLayers();
            loadCitiesInBounds();
            showPanel('panelNational');
            updateBreadcrumb('national');
            updateModeHint('💡 地级市 · 点击城市查看详情，继续放大查看区县');
            break;

        case 'district':
            // 区县标记 — 显示视口内的区县
            provinceLayer.clearLayers();
            cityLayer.clearLayers();
            loadDistrictsInBounds();
            showPanel('panelNational');
            updateBreadcrumb('national');
            updateModeHint('💡 区县视图 · 点击区县查看详情');
            break;

        case 'detail':
            // 详细视图 — 仅显示研究点
            provinceLayer.clearLayers();
            cityLayer.clearLayers();
            districtLayer.clearLayers();
            updateModeHint('💡 详细视图 · 显示遥感研究数据点');
            break;
    }

    setTimeout(() => { mapState.isTransitioning = false; }, 400);
}

function handleFocusedZoomChange(newZoom) {
    const level = mapState.focusedLevel;

    if (level === 'province') {
        if (newZoom < 6) {
            exitToAutoMode();
            return;
        }
        if (newZoom >= 10) {
            // 在省份聚焦模式下放大—加载该省的区县
            loadDistrictsForFocusedProvince(mapState.currentProvinceName);
        } else {
            districtLayer.clearLayers();
        }
    }

    if (level === 'city') {
        if (newZoom < 7) {
            // 缩小太多—返回省份
            if (mapState.currentProvinceName) {
                enterProvince(mapState.currentProvinceName);
            } else {
                exitToAutoMode();
            }
            return;
        }
        if (newZoom >= 10) {
            // 在城市聚焦模式下放大—显示该城区县
            loadDistrictsForCity(mapState.currentCityId);
        } else {
            districtLayer.clearLayers();
        }
    }
}

function exitToAutoMode() {
    mapState.displayMode = 'auto';
    mapState.focusedLevel = null;
    mapState.mode = 'national';
    mapState.currentProvinceName = null;
    mapState.currentCityId = null;

    cityLayer.clearLayers();
    provinceLayer.clearLayers();
    districtLayer.clearLayers();

    const zoom = Math.round(map.getZoom());
    mapState.previousZoom = zoom;
    const level = getLevelFromZoom(zoom);
    mapState.autoLevel = level;
    handleAutoZoomChange(zoom, zoom);

    showPanel('panelNational');
    updateBreadcrumb('national');
}

function getMapBounds() {
    const b = map.getBounds();
    return {
        min_lat: b.getSouth(),
        max_lat: b.getNorth(),
        min_lng: b.getWest(),
        max_lng: b.getEast()
    };
}

function loadCitiesInBounds() {
    if (!mapState.allCitiesData || mapState.allCitiesData.length === 0) return;
    const bounds = getMapBounds();
    // 略微扩展范围以避免边缘闪烁
    const pad = 0.3;
    const visibleCities = mapState.allCitiesData.filter(c =>
        c.latitude >= bounds.min_lat - pad && c.latitude <= bounds.max_lat + pad &&
        c.longitude >= bounds.min_lng - pad && c.longitude <= bounds.max_lng + pad
    );

    if (visibleCities.length > 0) {
        renderCityMarkers(visibleCities);
    }
}

function refreshBoundsContent() {
    if (mapState.autoLevel === 'city') {
        loadCitiesInBounds();
    } else if (mapState.autoLevel === 'district') {
        loadDistrictsInBounds();
    }
}

async function loadDistrictsInBounds() {
    const bounds = getMapBounds();
    mapState.boundsRequestId++;
    const currentRequestId = mapState.boundsRequestId;

    // 从全部城市中找到视口内的城市
    const allCities = mapState.allCitiesData;
    if (!allCities || allCities.length === 0) return;

    const pad = 0.5;
    const visibleCities = allCities.filter(c =>
        c.latitude >= bounds.min_lat - pad && c.latitude <= bounds.max_lat + pad &&
        c.longitude >= bounds.min_lng - pad && c.longitude <= bounds.max_lng + pad
    );

    // 检查缓存，找出未缓存的city_id
    const uncachedCityIds = visibleCities
        .filter(c => !mapState.districtsByCity[c.id])
        .map(c => c.id);

    // 批量加载未缓存城市的区县
    if (uncachedCityIds.length > 0) {
        try {
            // 逐一加载（简化处理，避免URL过长）
            for (const cid of uncachedCityIds.slice(0, 10)) {
                const url = '/api/districts?city_id=' + cid;
                const districts = await fetchJSON(url);
                mapState.districtsByCity[cid] = districts;
            }
        } catch (e) {
            console.error('加载区县数据失败:', e);
        }
    }

    if (currentRequestId !== mapState.boundsRequestId) return; // 过期请求

    // 收集视口内所有区县
    let allVisibleDistricts = [];
    visibleCities.forEach(c => {
        const cached = mapState.districtsByCity[c.id] || [];
        allVisibleDistricts = allVisibleDistricts.concat(cached);
    });

    // 严格范围过滤
    allVisibleDistricts = allVisibleDistricts.filter(d =>
        d.latitude >= bounds.min_lat && d.latitude <= bounds.max_lat &&
        d.longitude >= bounds.min_lng && d.longitude <= bounds.max_lng
    );

    renderDistrictMarkers(allVisibleDistricts.length > 0 ? allVisibleDistricts : []);
}

async function loadDistrictsForFocusedProvince(provinceName) {
    const cacheKey = '__province_' + provinceName;
    if (mapState.districtsByCity[cacheKey]) {
        renderDistrictMarkers(mapState.districtsByCity[cacheKey]);
        return;
    }
    try {
        const districts = await fetchJSON('/api/districts?province=' + encodeURIComponent(provinceName));
        mapState.districtsByCity[cacheKey] = districts;
        // 同时按city_id缓存
        districts.forEach(d => {
            if (!mapState.districtsByCity[d.city_id]) mapState.districtsByCity[d.city_id] = [];
            mapState.districtsByCity[d.city_id].push(d);
        });
        renderDistrictMarkers(districts);
    } catch (e) {
        console.error('加载省份区县失败:', e);
    }
}

async function loadDistrictsForCity(cityId) {
    if (mapState.districtsByCity[cityId]) {
        renderDistrictMarkers(mapState.districtsByCity[cityId]);
        return;
    }
    try {
        const districts = await fetchJSON('/api/districts?city_id=' + cityId);
        mapState.districtsByCity[cityId] = districts;
        renderDistrictMarkers(districts);
    } catch (e) {
        console.error('加载城市区县失败:', e);
    }
}

// ==================== 区县详情 ====================

async function enterDistrict(districtId, lat, lng) {
    mapState.displayMode = 'focused';
    mapState.focusedLevel = 'district';

    map.flyTo([lat, lng], 13, { duration: 0.8 });

    setLoading('panelDistrict', true);
    showPanel('panelDistrict');

    try {
        const detail = await fetchJSON('/api/district/' + districtId);
        if (!detail) throw new Error('No data');
        fillDistrictPanel(detail);
        setLoading('panelDistrict', false);

        updateBreadcrumb('district', detail.province_name, detail.city_name, detail.name);
        updateModeHint(`💡 当前显示：${detail.name} · ${detail.type || '区县'} · ${detail.city_name}`);

        showDistrictPopup(detail, lat, lng);
    } catch (e) {
        showError('加载区县详情失败');
        setLoading('panelDistrict', false);
    }
}

function showDistrictPopup(detail, lat, lng) {
    map.closePopup();
    const popupHtml = `
        <div class="popup-content">
            <div class="popup-header popup-district-header">
                <h3>${detail.name}</h3>
                <div class="popup-badges">
                    <span class="popup-badge">📍 ${detail.city_name}</span>
                    <span class="popup-badge">🏷️ ${detail.type || '区县'}</span>
                </div>
            </div>
            <div class="popup-body">
                <div class="popup-field"><span class="popup-label">人口：</span>${detail.population || '-'} 万</div>
                <div class="popup-field"><span class="popup-label">面积：</span>${detail.area ? detail.area.toLocaleString() : '-'} km²</div>
                <div class="popup-field"><span class="popup-label">所属省份：</span>${detail.province_name}</div>
            </div>
        </div>
    `;
    L.popup({ maxWidth: 320, className: 'custom-popup' })
        .setLatLng([lat, lng])
        .setContent(popupHtml)
        .openOn(map);
}

function fillDistrictPanel(d) {
    document.getElementById('districtName').textContent = d.name;
    document.getElementById('districtType').textContent = d.type || '-';
    document.getElementById('districtCity').textContent = d.city_name || '-';
    document.getElementById('districtProvince').textContent = d.province_name || '-';
    document.getElementById('districtPopulation').textContent = d.population ? d.population + ' 万' : '-';
    document.getElementById('districtArea').textContent = d.area ? d.area.toLocaleString() + ' km²' : '-';

    const backBtn = document.getElementById('btnBackFromDistrict');
    if (backBtn) {
        backBtn.textContent = '← 返回' + (d.city_name || '上级');
    }
}

// ==================== 遥感研究详情卡片 ====================

/**
 * 解析研究概述文本，提取【】标记的章节
 * 返回: [{category: '中文类别名', key: 'section_key', icon: 'emoji', cssClass: 'rs-bg-xxx', content: '...'}]
 */
function parseResearchOverview(overview) {
    const sections = [];
    // 匹配 【分类名】 后跟内容（直到下一个【或结尾）
    const regex = /【([^】]+)】([\s\S]*?)(?=【|$)/g;
    let match;

    while ((match = regex.exec(overview)) !== null) {
        const rawCategory = match[1].trim();
        const content = match[2].trim();
        const sectionInfo = classifySection(rawCategory);
        sections.push({
            category: rawCategory,
            icon: sectionInfo.icon,
            cssClass: sectionInfo.cssClass,
            content: content,
            key: sectionInfo.key
        });
    }

    // 如果没有找到【】标记，整体作为一个章节
    if (sections.length === 0 && overview.trim()) {
        sections.push({
            category: '研究概述',
            icon: '📝',
            cssClass: 'rs-bg-gray',
            content: overview.trim(),
            key: 'overview'
        });
    }

    return sections;
}

/**
 * 根据分类名匹配图标和颜色
 */
function classifySection(category) {
    const name = category.toLowerCase();
    if (name.includes('背景') || name.includes('意义') || name.includes('问题')) {
        return { key: 'background', icon: '🌍', cssClass: 'rs-bg-purple' };
    }
    if (name.includes('技术') || name.includes('体系') || name.includes('架构') || name.includes('核心')) {
        return { key: 'technology', icon: '⚙️', cssClass: 'rs-bg-blue' };
    }
    if (name.includes('方法') || name.includes('算法') || name.includes('反演') || name.includes('参数')) {
        return { key: 'method', icon: '🔬', cssClass: 'rs-bg-teal' };
    }
    if (name.includes('数据') || name.includes('验证') || name.includes('实测') || name.includes('精度')) {
        return { key: 'data', icon: '📊', cssClass: 'rs-bg-orange' };
    }
    if (name.includes('成果') || name.includes('应用') || name.includes('结果') || name.includes('案例') || name.includes('效果')) {
        return { key: 'results', icon: '🏆', cssClass: 'rs-bg-green' };
    }
    if (name.includes('价值') || name.includes('前景') || name.includes('展望') || name.includes('意义') || name.includes('创新')) {
        return { key: 'impact', icon: '💡', cssClass: 'rs-bg-red' };
    }
    return { key: 'general', icon: '📋', cssClass: 'rs-bg-gray' };
}

/**
 * 格式化章节内容：识别列表项、子标题、数据指标等
 */
function formatSectionContent(content) {
    if (!content) return '';

    // 转义HTML
    let html = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // 换行 → <br>
    html = html.replace(/\n/g, '<br>');

    // 识别 ▶ 开头的子标题
    html = html.replace(/(?:<br>|^)\s*▶\s*([^：:]+)[：:]/g,
        '<br><strong style="color:#2c3e50;">📌 $1：</strong>');

    // 识别 (1)(2)(3) 等编号
    html = html.replace(/（(\d+)）/g, '<strong>($1)</strong>');

    // 识别 R², RMSE 等技术指标
    html = html.replace(/(R²\s*[>&lt;]+\s*[\d.]+)/g,
        '<span class="research-method-tag highlight">$1</span>');
    html = html.replace(/(RMSE\s*[>&lt;]+\s*[\d.]+[\w\/]+)/g,
        '<span class="research-method-tag highlight">$1</span>');

    // 识别百分比
    html = html.replace(/([&lt;>]\s*\d+%)/g,
        '<span class="research-method-tag highlight">$1</span>');

    return html;
}

/**
 * 打开遥感研究详情卡片
 */
async function showResearchDetailCard(point) {
    // 解析章节
    const sections = parseResearchOverview(point.overview);

    // 构建头部
    document.getElementById('researchTitle').textContent = point.title || '遥感研究数据点';
    document.getElementById('researchAuthor').textContent = '👤 ' + (point.author || '-');
    document.getElementById('researchInstitution').textContent = '🏛️ ' + (point.institution || '-');
    document.getElementById('researchYear').textContent = '📅 ' + (point.year || '-');
    document.getElementById('researchProvince').textContent = '📍 ' + (point.province || '-');

    // 构建分类章节
    const container = document.getElementById('researchSections');
    container.innerHTML = '';

    sections.forEach(sec => {
        const div = document.createElement('div');
        div.className = 'research-section';

        div.innerHTML = `
            <div class="research-section-head ${sec.cssClass}">
                <span class="section-icon">${sec.icon}</span>
                <span>${sec.category}</span>
            </div>
            <div class="research-section-body">
                ${formatSectionContent(sec.content)}
            </div>
        `;
        container.appendChild(div);
    });

    // 显示面板
    showPanel('panelResearch');
    document.getElementById('modeHint').textContent =
        '🛰️ 遥感研究案例 · ' + (point.title || '详情');
}

// ==================== 侧边栏面板 ====================

function showPanel(panelId) {
    ['panelNational', 'panelProvince', 'panelCity', 'panelDistrict', 'panelResearch'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = (id === panelId) ? '' : 'none';
    });
}

function fillProvincePanel(detail) {
    document.getElementById('provinceName').textContent = detail.name;
    document.getElementById('provinceAbbr').textContent = detail.abbreviation || '-';
    document.getElementById('provinceCapital').textContent = detail.capital || '-';
    document.getElementById('provincePopulation').textContent = detail.population ? detail.population + ' 万' : '-';
    document.getElementById('provinceArea').textContent = detail.area ? detail.area.toLocaleString() + ' km²' : '-';
    document.getElementById('provinceCityCount').textContent = detail.city_count + ' 个';
    document.getElementById('provinceIntro').textContent = detail.intro || '-';
    document.getElementById('provinceCulture').textContent = detail.culture || '-';

    // 城市列表
    const listEl = document.getElementById('cityList');
    listEl.innerHTML = '';
    detail.cities.forEach(c => {
        const item = document.createElement('div');
        item.className = 'city-list-item';
        const lvCls = (c.level && c.level.includes('省会')) || c.level === '直辖市' ? 'city-tag-capital' :
                       (c.level && c.level.includes('自治州')) ? 'city-tag-zizhi' : 'city-tag-normal';
        item.innerHTML = `
            <span class="city-list-name">${c.name}</span>
            <span class="city-tag ${lvCls}">${c.level || '地级市'}</span>
        `;
        item.addEventListener('click', () => enterCity(c.id, c.latitude, c.longitude));
        listEl.appendChild(item);
    });
}

function fillCityPanel(d) {
    document.getElementById('cityName').textContent = d.name;
    document.getElementById('cityLevel').textContent = d.level || '-';
    document.getElementById('cityProvince').textContent = d.province || '-';
    document.getElementById('cityPopulation').textContent = d.population ? d.population + ' 万' : '-';
    document.getElementById('cityArea').textContent = d.area ? d.area.toLocaleString() + ' km²' : '-';
    document.getElementById('cityGDP').textContent = d.gdp ? d.gdp.toLocaleString() + ' 亿元' : '-';
    document.getElementById('cityEstablished').textContent = d.established || '-';
    document.getElementById('cityClimate').textContent = d.climate || '-';
    document.getElementById('cityIntro').textContent = d.intro || '-';
    document.getElementById('cityCulture').textContent = d.culture || '-';
    document.getElementById('cityAttractions').textContent = d.attractions || '-';

    // 更新返回按钮文字
    const backBtn = document.getElementById('btnBackFromCity');
    const provinceName = mapState.currentProvinceName || d.province;
    backBtn.textContent = '← 返回' + provinceName;
}

// ==================== 面包屑导航 ====================

function updateBreadcrumb(level, province, city, district) {
    const bcSep1 = document.getElementById('bcSep1');
    const bcSep2 = document.getElementById('bcSep2');
    const bcProvince = document.getElementById('bcProvince');
    const bcCity = document.getElementById('bcCity');
    const bcSep3 = document.getElementById('bcSep3');
    const bcDistrict = document.getElementById('bcDistrict');

    // 隐藏所有
    [bcSep1, bcSep2, bcProvince, bcCity].forEach(el => { if (el) el.style.display = 'none'; });
    if (bcSep3) bcSep3.style.display = 'none';
    if (bcDistrict) bcDistrict.style.display = 'none';

    if (level === 'national') {
        // 全部隐藏
    } else if (level === 'province') {
        bcSep1.style.display = '';
        bcProvince.style.display = '';
        bcProvince.textContent = province;
    } else if (level === 'city') {
        bcSep1.style.display = '';
        bcProvince.style.display = '';
        bcProvince.textContent = province;
        bcSep2.style.display = '';
        bcCity.style.display = '';
        bcCity.textContent = city;
    } else if (level === 'district') {
        bcSep1.style.display = '';
        bcProvince.style.display = '';
        bcProvince.textContent = province;
        bcSep2.style.display = '';
        bcCity.style.display = '';
        bcCity.textContent = city;
        if (bcSep3) bcSep3.style.display = '';
        if (bcDistrict) { bcDistrict.style.display = ''; bcDistrict.textContent = district; }
    }
}

function updateModeHint(text) {
    document.getElementById('modeHint').textContent = text;
}

// ==================== 全局统计 ====================

async function updateGlobalStats() {
    const stats = await loadStats();
    if (!stats) return;

    document.getElementById('statProvinces').textContent = stats.province_count;
    document.getElementById('statCities').textContent = stats.city_count;
    document.getElementById('statResearch').textContent = stats.research_count;
    document.getElementById('statYearRange').textContent =
        (stats.year_min && stats.year_max) ? stats.year_min + '-' + stats.year_max : '-';

    document.getElementById('headerTotal').textContent =
        `共 ${stats.province_count} 省 · ${stats.city_count} 市 · ${stats.research_count} 遥感数据点`;
}

// ==================== 快速跳转下拉框 ====================

function fillProvinceSelect() {
    const select = document.getElementById('provinceSelect');
    select.innerHTML = '<option value="">-- 选择省份 --</option>';
    mapState.provincesData.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.name;
        opt.textContent = p.name + ' (' + p.city_count + ' 市)';
        select.appendChild(opt);
    });
    select.addEventListener('change', e => {
        if (e.target.value) {
            enterProvince(e.target.value);
            e.target.value = '';
        }
    });
}

// ==================== 搜索功能 ====================

let searchTimer = null;
let searchActiveIndex = -1;  // 键盘导航当前高亮索引

function setupSearch() {
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');

    input.addEventListener('input', () => {
        clearTimeout(searchTimer);
        const q = input.value.trim();
        if (!q) {
            closeSearchResults();
            return;
        }
        searchTimer = setTimeout(() => doSearch(q), 250);
    });

    // 键盘导航
    input.addEventListener('keydown', e => {
        const items = results.querySelectorAll('.search-item');
        if (items.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                searchActiveIndex = Math.min(searchActiveIndex + 1, items.length - 1);
                updateSearchHighlight(items);
                break;
            case 'ArrowUp':
                e.preventDefault();
                searchActiveIndex = Math.max(searchActiveIndex - 1, 0);
                updateSearchHighlight(items);
                break;
            case 'Enter':
                e.preventDefault();
                if (searchActiveIndex >= 0 && searchActiveIndex < items.length) {
                    items[searchActiveIndex].click();
                }
                break;
            case 'Escape':
                e.preventDefault();
                closeSearchResults();
                input.blur();
                break;
        }
    });

    // 点击外部关闭
    document.addEventListener('click', e => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            closeSearchResults();
        }
    });

    input.addEventListener('focus', () => {
        if (results.children.length > 0) {
            results.style.display = 'block';
        }
    });
}

async function doSearch(q) {
    const results = document.getElementById('searchResults');
    searchActiveIndex = -1;

    try {
        const list = await fetchJSON('/api/search?q=' + encodeURIComponent(q));
        results.innerHTML = '';

        if (list.length === 0) {
            results.innerHTML = '<div class="search-item search-empty">未找到匹配结果</div>';
        } else {
            list.forEach((item, idx) => {
                const div = document.createElement('div');
                div.className = 'search-item';
                div.dataset.index = idx;

                if (item.type === 'province') {
                    // 省份结果
                    div.innerHTML = `
                        <span class="search-name">
                            <span class="search-type-icon">🏛️</span> ${highlightMatch(item.name, q)}
                        </span>
                        <span class="search-meta">${item.capital || ''} · ${item.city_count} 市</span>
                    `;
                    div.addEventListener('click', async () => {
                        closeSearchResults();
                        document.getElementById('searchInput').value = '';
                        await enterProvince(item.name);
                    });
                } else if (item.type === 'district') {
                    // 区县结果
                    div.innerHTML = `
                        <span class="search-name">
                            <span class="search-type-icon">🏘️</span> ${highlightMatch(item.name, q)}
                        </span>
                        <span class="search-meta">${item.city_name || ''} · ${item.province} · ${item.district_type || '区县'}</span>
                    `;
                    div.addEventListener('click', async () => {
                        const provinceName = item.province;
                        const cityId = item.city_id;
                        closeSearchResults();
                        document.getElementById('searchInput').value = '';

                        // 先进入省份
                        if (provinceName !== mapState.currentProvinceName) {
                            await enterProvince(provinceName);
                            await new Promise(r => setTimeout(r, 600));
                        }
                        // 确保城市标记已渲染
                        if (cityId && cityLayer.getLayers().length === 0 && mapState.currentProvinceName) {
                            const cities = await loadCitiesByProvince(mapState.currentProvinceName);
                            if (cities.length > 0) renderCityMarkers(cities);
                        }
                        // 加载并显示该城区县，然后聚焦到区县
                        await loadDistrictsForCity(cityId);
                        await enterDistrict(item.id, item.latitude, item.longitude);
                    });
                } else {
                    // 城市结果
                    div.innerHTML = `
                        <span class="search-name">
                            <span class="search-type-icon">🏙️</span> ${highlightMatch(item.name, q)}
                        </span>
                        <span class="search-meta">${item.province} · ${item.level || '地级市'}</span>
                    `;
                    div.addEventListener('click', async () => {
                        const provinceName = item.province;
                        closeSearchResults();
                        document.getElementById('searchInput').value = '';

                        // 先进入省份（如果不在该省份），再进入城市
                        if (provinceName !== mapState.currentProvinceName) {
                            await enterProvince(provinceName);
                            // 短暂等待地图动画完成后进入城市
                            await new Promise(r => setTimeout(r, 600));
                        }
                        await enterCity(item.id, item.latitude, item.longitude);
                    });
                }
                results.appendChild(div);
            });

            // 如果只有一个结果且是精确匹配，自动高亮
            if (list.length === 1) {
                searchActiveIndex = 0;
                const firstItem = results.querySelector('.search-item');
                if (firstItem) firstItem.classList.add('search-highlight');
            }
        }
        results.style.display = 'block';
    } catch (e) {
        console.error('搜索失败：', e);
        results.innerHTML = '<div class="search-item search-empty">搜索失败，请重试</div>';
        results.style.display = 'block';
    }
}

function highlightMatch(text, query) {
    // 高亮匹配的文字
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escaped})`, 'gi');
    return text.replace(regex, '<mark class="search-highlight-text">$1</mark>');
}

function updateSearchHighlight(items) {
    items.forEach((item, idx) => {
        if (idx === searchActiveIndex) {
            item.classList.add('search-highlight');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('search-highlight');
        }
    });
}

function closeSearchResults() {
    const results = document.getElementById('searchResults');
    results.innerHTML = '';
    results.style.display = 'none';
    searchActiveIndex = -1;
}

// ==================== 错误提示 ====================

function showError(msg) {
    // 移除已有的错误提示
    const existing = document.querySelector('.error-toast');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.className = 'error-toast';
    div.textContent = '⚠️ ' + msg;
    document.body.appendChild(div);
    setTimeout(() => {
        div.classList.add('fade-out');
        setTimeout(() => div.remove(), 500);
    }, 3500);
}

// ==================== 侧边栏折叠 ====================

function setupSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const showBtn = document.getElementById('showSidebar');
    const toggleBtn = document.getElementById('toggleSidebar');

    function toggle() {
        if (sidebar.style.display === 'none') {
            sidebar.style.display = '';
            showBtn.style.display = 'none';
            toggleBtn.style.display = '';
        } else {
            sidebar.style.display = 'none';
            showBtn.style.display = 'block';
            toggleBtn.style.display = 'none';
        }
        setTimeout(() => map.invalidateSize(), 300);
    }

    showBtn.addEventListener('click', toggle);
    toggleBtn.addEventListener('click', toggle);
}

// ==================== 图层开关 ====================

function setupLayerToggles() {
    document.getElementById('toggleProvinces').addEventListener('change', e => {
        showProvinces = e.target.checked;
        if (mapState.displayMode === 'auto' && mapState.autoLevel === 'province') {
            if (showProvinces) {
                renderProvinceMarkers(mapState.provincesData);
            } else {
                provinceLayer.clearLayers();
            }
        } else if (mapState.mode === 'national') {
            if (showProvinces) {
                renderProvinceMarkers(mapState.provincesData);
            } else {
                provinceLayer.clearLayers();
            }
        }
    });

    document.getElementById('toggleResearch').addEventListener('change', async e => {
        showResearch = e.target.checked;
        if (showResearch) {
            const points = await loadResearchPoints(
                mapState.mode === 'province' ? mapState.currentProvinceName : null
            );
            renderResearchPoints(points);
        } else {
            researchLayer.clearLayers();
        }
    });
}

// ==================== 面包屑事件 ====================

function setupBreadcrumbEvents() {
    document.querySelectorAll('.bc-link').forEach(el => {
        el.addEventListener('click', () => {
            const level = el.dataset.level;
            if (level === 'national') enterNational();
            else if (level === 'province' && mapState.currentProvinceName) {
                enterProvince(mapState.currentProvinceName);
            }
        });
    });
}

// ==================== 返回按钮事件 ====================

function setupBackButtons() {
    document.getElementById('btnBackFromProvince').addEventListener('click', enterNational);
    document.getElementById('btnBackFromCity').addEventListener('click', () => {
        if (mapState.currentProvinceName) {
            enterProvince(mapState.currentProvinceName);
        } else {
            enterNational();
        }
    });
}

// ==================== 应用启动 ====================

async function initApp() {
    initMap();

    // 并行加载基础数据
    await Promise.all([
        loadProvinces().then(provinces => {
            renderProvinceMarkers(provinces);
            fillProvinceSelect();
        }),
        updateGlobalStats(),
        loadResearchPoints().then(points => renderResearchPoints(points))
    ]);

    // 加载全部城市数据（用于缩放自适应范围筛选）
    try {
        mapState.allCitiesData = await fetchJSON('/api/cities');
    } catch (e) {
        console.error('加载全部城市失败:', e);
    }

    // 启用缩放自适应处理器
    setupZoomHandler();

    // 绑定 UI 事件
    setupSidebarToggle();
    setupLayerToggles();
    setupBreadcrumbEvents();
    setupBackButtons();
    setupSearch();

    // 区县返回按钮
    const btnBackDistrict = document.getElementById('btnBackFromDistrict');
    if (btnBackDistrict) {
        btnBackDistrict.addEventListener('click', () => {
            if (mapState.currentCityId && mapState.currentProvinceName) {
                enterProvince(mapState.currentProvinceName);
            } else if (mapState.currentProvinceName) {
                enterProvince(mapState.currentProvinceName);
            } else {
                exitToAutoMode();
            }
        });
    }

    // 遥感研究详情返回按钮
    const btnBackResearch = document.getElementById('btnBackFromResearch');
    if (btnBackResearch) {
        btnBackResearch.addEventListener('click', () => {
            // 返回之前的视图面板
            if (mapState.mode === 'city') {
                showPanel('panelCity');
            } else if (mapState.mode === 'province') {
                showPanel('panelProvince');
            } else {
                showPanel('panelNational');
            }
            // 恢复之前的模式提示
            if (mapState.mode === 'city' && mapState.currentProvinceName) {
                updateModeHint(`💡 当前显示：${mapState.currentProvinceName} · 点击城市标记可查看详细介绍`);
            } else if (mapState.mode === 'province') {
                updateModeHint(`💡 当前显示：${mapState.currentProvinceName} · 点击城市标记查看详情`);
            } else {
                updateModeHint('💡 全国省份 · 滚动放大查看地级市，继续放大查看区县');
            }
        });
    }

    // 窗口大小自适应
    window.addEventListener('resize', () => map && map.invalidateSize());

    // 初始化自动级别
    mapState.autoLevel = 'province';
    mapState.previousZoom = CHINA_ZOOM;

    console.log('🚀 中国行政区划 + 遥感数据地图 已就绪（含缩放自适应+区县级）');
}

document.addEventListener('DOMContentLoaded', initApp);
