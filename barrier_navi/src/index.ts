/**
 * バリアナビ（身体障害向け）フロントエンド
 */

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  count?: number;
  total_count?: number; // ★追加：全件数を受け取る
  error?: string;
}

interface BodyScoreSummary {
  met_items: number;
  total_items: number;
  percentage: number;
  label: string;
}

interface BodyStationSummary {
  station_id: number;
  station_name: string;
  prefecture: string;
  city: string;
  operator: string;
  line_name: string;
  score: BodyScoreSummary;
}

interface BodyMetricDetail {
  key: string;
  label: string;
  value: number | string | null;
  raw_value: number | string | null;
  ratio: number;
  met: boolean;
  type: string;
}

interface BodyStationDetail extends BodyStationSummary {
  metrics: BodyMetricDetail[];
}

interface BodyMetricDefinition {
  key: string;
  label: string;
  required: number;
  type: 'flag' | 'number';
}

const BODY_METRICS: BodyMetricDefinition[] = [
  // フラグ型（〇×で表せる項目）：設置されていれば1点
  { key: 'step_response_status', label: '段差への対応', required: 1, type: 'flag' },
  { key: 'has_guidance_system', label: '案内設備の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_restroom', label: '障害者対応型便所の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_gate', label: '障害者対応型改札口の設置の有無', required: 1, type: 'flag' },
  { key: 'has_fall_prevention', label: '転落防止のための設備の設置の有無', required: 1, type: 'flag' },
  // 数値型（基準値以上であれば1点、未満なら0点）
  { key: 'num_platforms', label: 'プラットホームの数', required: 6, type: 'number' },
  { key: 'num_step_free_platforms', label: '段差が解消されているプラットホームの数', required: 6, type: 'number' },
  { key: 'num_elevators', label: 'エレベーターの設置基数', required: 4, type: 'number' },
  { key: 'num_compliant_elevators', label: '移動等円滑化基準に適合しているエレベーターの設置基数', required: 4, type: 'number' },
  { key: 'num_escalators', label: 'エスカレーターの設置基数', required: 4, type: 'number' },
  { key: 'num_compliant_escalators', label: '移動等円滑化基準に適合しているエスカレーターの設置基数', required: 4, type: 'number' },
  { key: 'num_other_lifts', label: 'その他の昇降機の設置基数', required: 2, type: 'number' },
  { key: 'num_slopes', label: '傾斜路の設置箇所数', required: 2, type: 'number' },
  { key: 'num_compliant_slopes', label: '移動等円滑化基準に適合している傾斜路の設置箇所数', required: 2, type: 'number' },
  { key: 'num_wheelchair_accessible_platforms', label: '車いす使用者の円滑な乗降が可能なプラットホームの数', required: 6, type: 'number' }
];


class StationApp {
  private apiBaseUrl = 'http://localhost:5000/api';
  private currentPage = 1;
  private pageSize = 10;
  private selectedPrefecture: string | null = null;
  private keyword: string = '';
  private lastResultCount = 0;
  private totalCount = 0; // ★追加：全件数を保存
  private selectedFilters: string[] = [];
  private sortOrder: 'none' | 'score-asc' | 'score-desc' = 'none';

  constructor() {
    this.init();
  }

  private async init(): Promise<void> {
    this.renderFilterControls();
    this.setupEventListeners();
    await this.loadPrefectures();
    await this.fetchLines();
    await this.loadStations();
  }

  private renderFilterControls(): void {
    const container = document.getElementById('filter-list');
    if (!container) return;
    container.innerHTML = '';

    BODY_METRICS.forEach((metric) => {
      const item = document.createElement('div');
      item.className = 'filter-item';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `filter-${metric.key}`;
      checkbox.dataset.metricKey = metric.key;
      checkbox.className = 'filter-checkbox';

      const label = document.createElement('label');
      label.htmlFor = `filter-${metric.key}`;
      label.textContent = metric.label;

      checkbox.addEventListener('change', () => {
        this.currentPage = 1;
        this.loadStations();
      });

      item.appendChild(checkbox);
      item.appendChild(label);
      container.appendChild(item);
    });
  }

  private setupEventListeners(): void {
    const searchButton = document.getElementById('search-btn') as HTMLButtonElement | null;
    const searchInput = document.getElementById('search-input') as HTMLInputElement | null;
    const prefectureSelect = document.getElementById('prefecture-select') as HTMLSelectElement | null;
    const sortSelect = document.getElementById('sort-select') as HTMLSelectElement | null;
    
    // ページネーションボタン
    const prevButton = document.getElementById('prev-btn') as HTMLButtonElement | null;
    const nextButton = document.getElementById('next-btn') as HTMLButtonElement | null;
    const firstButton = document.getElementById('first-btn') as HTMLButtonElement | null; // ★追加
    const lastButton = document.getElementById('last-btn') as HTMLButtonElement | null;   // ★追加

    const filterButton = document.getElementById('apply-filter-btn') as HTMLButtonElement | null;
    const resetButton = document.getElementById('reset-filter-btn') as HTMLButtonElement | null;

    const lineSelect = document.getElementById('line-select') as HTMLSelectElement | null;

    searchButton?.addEventListener('click', () => this.applySearch());
    searchInput?.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') this.applySearch();
    });

    prefectureSelect?.addEventListener('change', (event) => {
      this.selectedPrefecture = (event.target as HTMLSelectElement).value || null;
      this.currentPage = 1;
      this.loadStations();
    });

    sortSelect?.addEventListener('change', (event) => {
      const value = (event.target as HTMLSelectElement).value;
      this.sortOrder = value as 'none' | 'score-asc' | 'score-desc';
      this.currentPage = 1;
      this.loadStations();
    });

    prevButton?.addEventListener('click', () => {
      if (this.currentPage > 1) {
        this.currentPage -= 1;
        this.loadStations();
      }
    });

    nextButton?.addEventListener('click', () => {
      // 次のページへ（総ページ数計算はloadStations後のtotalCountに依存しますが、簡易的なチェックとしてlastResultCountも使用可能）
      // updatePaginationで制御されているため、ここではシンプルに加算
      this.currentPage += 1;
      this.loadStations();
    });

    // ★追加: 最初へボタンの処理
    firstButton?.addEventListener('click', () => {
      this.currentPage = 1;
      this.loadStations();
    });

    // ★追加: 最後へボタンの処理
    lastButton?.addEventListener('click', () => {
      const totalPages = Math.ceil(this.totalCount / this.pageSize);
      this.currentPage = totalPages > 0 ? totalPages : 1;
      this.loadStations();
    });

    filterButton?.addEventListener('click', () => {
      this.currentPage = 1;
      this.loadStations();
    });

    resetButton?.addEventListener('click', () => {
      this.resetFilters();
    });

    lineSelect?.addEventListener('change', () => {
      this.currentPage = 1;
      this.loadStations();
    });
  }

  private applySearch(): void {
    const searchInput = document.getElementById('search-input') as HTMLInputElement | null;
    this.keyword = searchInput?.value.trim() || '';
    this.currentPage = 1;
    this.loadStations();
  }

  private resetFilters(): void {
    // 都道府県をリセット
    const prefectureSelect = document.getElementById('prefecture-select') as HTMLSelectElement | null;
    if (prefectureSelect) {
      prefectureSelect.value = '';
      this.selectedPrefecture = null;
    }

    // すべてのチェックボックスをリセット
    const checkboxes = document.querySelectorAll<HTMLInputElement>('.filter-checkbox');
    checkboxes.forEach((checkbox) => {
      checkbox.checked = false;
    });
    this.selectedFilters = [];

    // 検索キーワードをリセット
    const searchInput = document.getElementById('search-input') as HTMLInputElement | null;
    if (searchInput) {
      searchInput.value = '';
      this.keyword = '';
    }

    // ソートをリセット
    const sortSelect = document.getElementById('sort-select') as HTMLSelectElement | null;
    if (sortSelect) {
      sortSelect.value = 'none';
      this.sortOrder = 'none';
    }

    const lineSelect = document.getElementById('line-select') as HTMLSelectElement | null;
    if (lineSelect) {
      lineSelect.value = '';
    }

    // ページをリセットして再読み込み
    this.currentPage = 1;
    this.loadStations();

  }

  private collectFilters(): string[] {
    const checkboxes = document.querySelectorAll<HTMLInputElement>('.filter-checkbox:checked');
    const filters: string[] = [];
    checkboxes.forEach((checkbox) => {
      const metricKey = checkbox.dataset.metricKey;
      if (metricKey) {
        filters.push(metricKey);
      }
    });
    return filters;
  }

  private async loadPrefectures(): Promise<void> {
    const response = await this.fetchApi<Array<{ prefecture: string; count: number }>>('/stations/prefectures');
    if (response.success && response.data) {
      const select = document.getElementById('prefecture-select') as HTMLSelectElement | null;
      if (!select) return;
      select.innerHTML = '<option value="">都道府県</option>';
      response.data.forEach((item) => {
        const option = document.createElement('option');
        option.value = item.prefecture;
        option.textContent = `${item.prefecture} (${item.count}駅)`;
        select.appendChild(option);
      });
    }
  }

  private async fetchApi<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.apiBaseUrl}${endpoint}`);
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return { success: false, error: String(error) };
    }
  }

  private async loadStations(): Promise<void> {
    const loadingIndicator = document.getElementById('loading');
    const stationsContainer = document.getElementById('stations-list');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (stationsContainer) stationsContainer.innerHTML = '';

    this.selectedFilters = this.collectFilters();
    const params = new URLSearchParams({
      limit: this.pageSize.toString(),
      offset: ((this.currentPage - 1) * this.pageSize).toString()
    });

    if (this.selectedPrefecture) params.append('prefecture', this.selectedPrefecture);
    if (this.keyword) params.append('keyword', this.keyword);
    if (this.selectedFilters.length > 0) {
      params.append('filters', JSON.stringify(this.selectedFilters));
    }
    // ソート順をAPIに送信
    if (this.sortOrder !== 'none') {
      params.append('sort', this.sortOrder);
    }

    const lineSelect = document.getElementById('line-select') as HTMLSelectElement | null;
    if (lineSelect && lineSelect.value) {
        params.append('line_name', lineSelect.value);
    }

    const response = await this.fetchApi<BodyStationSummary[]>(`/body/stations?${params.toString()}`);

    if (loadingIndicator) loadingIndicator.style.display = 'none';

    if (response.success && response.data) {
      // バックエンドでソート済みなので、そのまま表示
      this.lastResultCount = response.data.length;
      this.totalCount = response.total_count || 0;

      this.renderStationCards(response.data);
      this.updatePagination();
      this.updateActiveFilters();
    } else if (stationsContainer) {
      stationsContainer.innerHTML = `<p class="error">データの取得に失敗しました: ${response.error}</p>`;
    }
  }

  private updateActiveFilters(): void {
    const container = document.getElementById('active-filters');
    const group = document.getElementById('active-filters-group');
    if (!container || !group) return;

    container.innerHTML = '';
    const hasFilters = this.selectedPrefecture || this.selectedFilters.length > 0 || this.keyword;

    if (!hasFilters) {
      group.style.display = 'none';
      return;
    }

    group.style.display = 'block';

    // 都道府県セクション
    if (this.selectedPrefecture) {
      const section = document.createElement('div');
      section.className = 'filter-section';
      section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">📍</span>
          <span class="filter-section-title">都道府県</span>
        </div>
        <div class="filter-chips">
          <div class="active-filter-chip filter-chip-prefecture">
            <span>${this.escapeHtml(this.selectedPrefecture)}</span>
            <button class="filter-remove-btn" data-type="prefecture" aria-label="削除">×</button>
          </div>
        </div>
      `;
      section.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
        const select = document.getElementById('prefecture-select') as HTMLSelectElement | null;
        if (select) {
          select.value = '';
          this.selectedPrefecture = null;
          this.currentPage = 1;
          this.loadStations();
        }
      });
      container.appendChild(section);
    }

    // 設備フィルタセクション
    if (this.selectedFilters.length > 0) {
      const section = document.createElement('div');
      section.className = 'filter-section';
      section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">🔧</span>
          <span class="filter-section-title">設備条件 <span class="filter-count">(${this.selectedFilters.length}件)</span></span>
        </div>
        <div class="filter-chips">
        </div>
      `;
      const chipsContainer = section.querySelector('.filter-chips');
      
      this.selectedFilters.forEach((filterKey) => {
        const metric = BODY_METRICS.find(m => m.key === filterKey);
        if (!metric) return;

        const chip = document.createElement('div');
        chip.className = 'active-filter-chip filter-chip-equipment';
        chip.innerHTML = `
          <span>${this.escapeHtml(metric.label)}</span>
          <button class="filter-remove-btn" data-type="filter" data-key="${filterKey}" aria-label="削除">×</button>
        `;
        chip.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
          const checkbox = document.querySelector(`#filter-${filterKey}`) as HTMLInputElement | null;
          if (checkbox) {
            checkbox.checked = false;
            this.currentPage = 1;
            this.loadStations();
          }
        });
        chipsContainer?.appendChild(chip);
      });
      container.appendChild(section);
    }

    // キーワード検索セクション
    if (this.keyword) {
      const section = document.createElement('div');
      section.className = 'filter-section';
      section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">🔍</span>
          <span class="filter-section-title">検索キーワード</span>
        </div>
        <div class="filter-chips">
          <div class="active-filter-chip filter-chip-keyword">
            <span>"${this.escapeHtml(this.keyword)}"</span>
            <button class="filter-remove-btn" data-type="keyword" aria-label="削除">×</button>
          </div>
        </div>
      `;
      section.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
        const input = document.getElementById('search-input') as HTMLInputElement | null;
        if (input) {
          input.value = '';
          this.keyword = '';
          this.currentPage = 1;
          this.loadStations();
        }
      });
      container.appendChild(section);
    }
  }

  private renderStationCards(stations: BodyStationSummary[]): void {
    const container = document.getElementById('stations-list');
    if (!container) return;

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

  private updatePagination(): void {
    const pageInfo = document.getElementById('page-info');
    const prevButton = document.getElementById('prev-btn') as HTMLButtonElement | null;
    const nextButton = document.getElementById('next-btn') as HTMLButtonElement | null;
    const firstButton = document.getElementById('first-btn') as HTMLButtonElement | null; // ★追加
    const lastButton = document.getElementById('last-btn') as HTMLButtonElement | null;   // ★追加

    // ★追加: 総ページ数の計算
    const totalPages = Math.ceil(this.totalCount / this.pageSize);

    if (pageInfo) pageInfo.textContent = `ページ ${this.currentPage} / ${totalPages || 1}`;

    const isFirstPage = this.currentPage === 1;
    const isLastPage = this.currentPage >= totalPages || totalPages === 0;

    if (prevButton) prevButton.disabled = isFirstPage;
    if (firstButton) firstButton.disabled = isFirstPage; // ★追加

    if (nextButton) nextButton.disabled = isLastPage;
    if (lastButton) lastButton.disabled = isLastPage;   // ★追加
  }

  private navigateToDetail(stationId: number): void {
    const url = new URL('detail.html', window.location.href);
    url.searchParams.set('stationId', stationId.toString());
    window.location.href = url.toString();
  }

  private escapeHtml(text: string | null | undefined): string {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private async fetchLines(): Promise<void> {
      const lineSelect = document.getElementById('line-select') as HTMLSelectElement;
      if (!lineSelect) return;

      try {
          const res = await fetch('http://localhost:5000/api/lines');
          const json = await res.json();

          if (json.success) {
              
              lineSelect.innerHTML = '<option value="">指定なし</option>';

              
              json.data.forEach((line: string) => {
                  const option = document.createElement('option');
                  option.value = line;
                  option.textContent = line;
                  lineSelect.appendChild(option);
              });
          }
      } catch (error) {
          console.error('Failed to fetch lines:', error);
      }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new StationApp();
});