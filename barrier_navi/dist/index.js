/**
 * バリアナビ（身体障害向け）フロントエンド
 */
const BODY_METRICS = [
    { key: 'step_response_status', label: '段差への対応', required: 1, type: 'flag' },
    { key: 'has_guidance_system', label: '案内設備の設置の有無', required: 1, type: 'flag' },
    { key: 'has_accessible_restroom', label: '障害者対応型便所の設置の有無', required: 1, type: 'flag' },
    { key: 'has_accessible_gate', label: '障害者対応型改札口の設置の有無', required: 1, type: 'flag' },
    { key: 'has_fall_prevention', label: '転落防止のための設備の設置の有無', required: 1, type: 'flag' },
    { key: 'num_platforms', label: 'プラットホームの数', required: 6, type: 'number' },
    { key: 'num_step_free_platforms', label: '段差が解消されているプラットホームの数', required: 6, type: 'number' },
    { key: 'num_elevators', label: 'エレベーターの設置基数', required: 4, type: 'number' },
    { key: 'num_compliant_elevators', label: '適合エレベーターの設置基数', required: 4, type: 'number' },
    { key: 'num_escalators', label: 'エスカレーターの設置基数', required: 4, type: 'number' },
    { key: 'num_compliant_escalators', label: '適合エスカレーターの設置基数', required: 4, type: 'number' },
    { key: 'num_other_lifts', label: 'その他の昇降機の設置基数', required: 2, type: 'number' },
    { key: 'num_slopes', label: '傾斜路の設置箇所数', required: 2, type: 'number' },
    { key: 'num_compliant_slopes', label: '適合傾斜路の設置箇所数', required: 2, type: 'number' },
    { key: 'num_wheelchair_accessible_platforms', label: '車いす乗降が可能なホーム数', required: 6, type: 'number' }
];
const WEIGHT_OPTIONS = [
    { label: '高', value: 3 },
    { label: '中', value: 2 },
    { label: '低', value: 1 }
];
class StationApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentPage = 1;
        this.pageSize = 10;
        this.selectedPrefecture = null;
        this.keyword = '';
        this.lastResultCount = 0;
        this.latestWeights = {};
        this.init();
    }
    async init() {
        this.renderWeightControls();
        this.setupEventListeners();
        await this.loadPrefectures();
        await this.loadStations();
    }
    renderWeightControls() {
        const container = document.getElementById('weight-list');
        if (!container)
            return;
        container.innerHTML = '';
        BODY_METRICS.forEach((metric) => {
            const item = document.createElement('div');
            item.className = 'weight-item';
            const label = document.createElement('span');
            label.textContent = metric.label;
            const select = document.createElement('select');
            select.dataset.metricKey = metric.key;
            select.className = 'weight-select';
            WEIGHT_OPTIONS.forEach((option) => {
                const opt = document.createElement('option');
                opt.value = option.value.toString();
                opt.textContent = option.label;
                if (option.value === 2)
                    opt.selected = true;
                select.appendChild(opt);
            });
            item.appendChild(label);
            item.appendChild(select);
            container.appendChild(item);
        });
    }
    setupEventListeners() {
        const searchButton = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');
        const prefectureSelect = document.getElementById('prefecture-select');
        const prevButton = document.getElementById('prev-btn');
        const nextButton = document.getElementById('next-btn');
        const filterButton = document.getElementById('apply-filter-btn');
        searchButton === null || searchButton === void 0 ? void 0 : searchButton.addEventListener('click', () => this.applySearch());
        searchInput === null || searchInput === void 0 ? void 0 : searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter')
                this.applySearch();
        });
        prefectureSelect === null || prefectureSelect === void 0 ? void 0 : prefectureSelect.addEventListener('change', (event) => {
            var _a;
            this.selectedPrefecture = ((_a = event.target) === null || _a === void 0 ? void 0 : _a.value) || null;
            this.currentPage = 1;
            this.loadStations();
        });
        prevButton === null || prevButton === void 0 ? void 0 : prevButton.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage -= 1;
                this.loadStations();
            }
        });
        nextButton === null || nextButton === void 0 ? void 0 : nextButton.addEventListener('click', () => {
            if (this.lastResultCount === this.pageSize) {
                this.currentPage += 1;
                this.loadStations();
            }
        });
        filterButton === null || filterButton === void 0 ? void 0 : filterButton.addEventListener('click', () => {
            this.currentPage = 1;
            this.loadStations();
        });
    }
    applySearch() {
        const searchInput = document.getElementById('search-input');
        this.keyword = (searchInput === null || searchInput === void 0 ? void 0 : searchInput.value.trim()) || '';
        this.currentPage = 1;
        this.loadStations();
    }
    collectWeights() {
        const selects = document.querySelectorAll('.weight-select');
        const weightMap = {};
        selects.forEach((select) => {
            const metricKey = select.dataset.metricKey;
            if (!metricKey)
                return;
            weightMap[metricKey] = Number(select.value) || 1;
        });
        return weightMap;
    }
    async loadPrefectures() {
        const response = await this.fetchApi('/stations/prefectures');
        if (response.success && response.data) {
            const select = document.getElementById('prefecture-select');
            if (!select)
                return;
            select.innerHTML = '<option value="">都道府県</option>';
            response.data.forEach((item) => {
                const option = document.createElement('option');
                option.value = item.prefecture;
                option.textContent = `${item.prefecture} (${item.count}駅)`;
                select.appendChild(option);
            });
        }
    }
    async fetchApi(endpoint) {
        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`);
            return await response.json();
        }
        catch (error) {
            console.error('API Error:', error);
            return { success: false, error: String(error) };
        }
    }
    async loadStations() {
        const loadingIndicator = document.getElementById('loading');
        const stationsContainer = document.getElementById('stations-list');
        if (loadingIndicator)
            loadingIndicator.style.display = 'block';
        if (stationsContainer)
            stationsContainer.innerHTML = '';
        this.latestWeights = this.collectWeights();
        const params = new URLSearchParams({
            limit: this.pageSize.toString(),
            offset: ((this.currentPage - 1) * this.pageSize).toString()
        });
        if (this.selectedPrefecture)
            params.append('prefecture', this.selectedPrefecture);
        if (this.keyword)
            params.append('keyword', this.keyword);
        if (Object.keys(this.latestWeights).length)
            params.append('weights', JSON.stringify(this.latestWeights));
        const response = await this.fetchApi(`/body/stations?${params.toString()}`);
        if (loadingIndicator)
            loadingIndicator.style.display = 'none';
        if (response.success && response.data) {
            this.lastResultCount = response.data.length;
            this.renderStationCards(response.data);
            this.updatePagination();
        }
        else if (stationsContainer) {
            stationsContainer.innerHTML = `<p class="error">データの取得に失敗しました: ${response.error}</p>`;
        }
    }
    renderStationCards(stations) {
        const container = document.getElementById('stations-list');
        if (!container)
            return;
        if (stations.length === 0) {
            container.innerHTML = '<p class="no-data">条件に一致する駅が見つかりませんでした。</p>';
            return;
        }
        container.innerHTML = '';
        stations.forEach((station) => {
            const card = document.createElement('div');
            card.className = 'station-card';
            card.innerHTML = `
        <div class="station-card__header">
          <span class="station-card__name">${this.escapeHtml(station.station_name)}</span>
          <span class="station-card__score">${station.score.label}</span>
        </div>
        <div class="station-card__meta">
          <span>${this.escapeHtml(station.prefecture)} ${this.escapeHtml(station.city || '')}</span>
          <span>${this.escapeHtml(station.operator)}</span>
        </div>
        <div class="station-card__progress">
          <div class="station-card__progress-bar" style="width:${station.score.percentage}%"></div>
        </div>
        <div class="station-card__footer">詳細を見る</div>
      `;
            card.addEventListener('click', () => this.navigateToDetail(station.station_id));
            container.appendChild(card);
        });
    }
    updatePagination() {
        const pageInfo = document.getElementById('page-info');
        const prevButton = document.getElementById('prev-btn');
        const nextButton = document.getElementById('next-btn');
        if (pageInfo)
            pageInfo.textContent = `ページ ${this.currentPage}`;
        if (prevButton)
            prevButton.disabled = this.currentPage === 1;
        if (nextButton)
            nextButton.disabled = this.lastResultCount < this.pageSize;
    }
    navigateToDetail(stationId) {
        const url = new URL('detail.html', window.location.href);
        url.searchParams.set('stationId', stationId.toString());
        if (Object.keys(this.latestWeights).length) {
            url.searchParams.set('weights', JSON.stringify(this.latestWeights));
        }
        window.location.href = url.toString();
    }
    escapeHtml(text) {
        if (!text)
            return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new StationApp();
});

