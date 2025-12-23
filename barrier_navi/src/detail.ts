// 型定義はそのまま使います
interface DetailApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

interface DetailScore {
  met_items: number;
  total_items: number;
  percentage: number;
  label: string;
}

interface DetailMetric {
  key: string;
  label: string;
  value: number | string | null;
  raw_value: number | string | null;
  required: number;
  ratio: number;
  met: boolean;
  type: string;
}

interface DetailStation {
  station_id: number;
  station_name: string;
  prefecture: string;
  city: string;
  operator: string;
  line_name: string;
  score: DetailScore;
  metrics: DetailMetric[];
}

class DetailPage {
  private apiBaseUrl = 'http://localhost:5000/api';
  private titleEl: HTMLElement | null = null;
  private scoreEl: HTMLElement | null = null;
  private metaEl: HTMLElement | null = null;
  private tableBodyEl: HTMLElement | null = null;

  // ★追加: 現在のモード
  private currentMode: 'body' | 'hearing' | 'vision' = 'body';

  constructor() {
    this.titleEl = document.getElementById('detail-title');
    this.scoreEl = document.getElementById('detail-score');
    this.metaEl = document.getElementById('detail-meta');
    this.tableBodyEl = document.getElementById('detail-table-body');

    // ★追加: モード判定
    const params = new URLSearchParams(window.location.search);
    const urlMode = params.get('mode');
    const bodyMode = document.body.dataset.mode;
    if (urlMode === 'hearing' || bodyMode === 'hearing') {
        this.currentMode = 'hearing';
    } else if (urlMode === 'vision' || bodyMode === 'vision') {
        this.currentMode = 'vision';
    } else {
        this.currentMode = 'body';
    }

    this.load();
  }

  private async load(): Promise<void> {
    const params = new URLSearchParams(window.location.search);
    const stationId = Number(params.get('stationId'));
    if (!stationId) {
      this.renderError('駅IDが指定されていません。');
      return;
    }

    // ★修正: モードに応じてAPIパスを切り替える
    const apiPath = this.currentMode === 'hearing' ? '/hearing/stations' : this.currentMode === 'vision' ? '/vision/stations' : '/body/stations';
    
    // 修正後:
    const response = await this.fetchApi<DetailStation>(`${apiPath}/${stationId}`);
    
    if (response.success && response.data) {
      this.renderDetail(response.data);
    } else {
      this.renderError(response.error || 'データを取得できませんでした。');
    }
  }

  private async fetchApi<T>(endpoint: string): Promise<DetailApiResponse<T>> {
    try {
      const res = await fetch(`${this.apiBaseUrl}${endpoint}`);
      return await res.json();
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  private renderDetail(detail: DetailStation): void {
    if (!this.titleEl || !this.scoreEl || !this.metaEl || !this.tableBodyEl) return;
    this.titleEl.textContent = detail.station_name;
    this.scoreEl.textContent = detail.score.label;
    const city = detail.city ? ` ${detail.city}` : '';
    this.metaEl.innerHTML = `
      <p>鉄道事業者: ${this.escape(detail.operator)}</p>
      <p>路線: ${this.escape(detail.line_name)}</p>
      <p>所在地: ${this.escape(detail.prefecture)}${this.escape(city)}</p>
    `;

    const rows = detail.metrics.map((metric) => {
      let valueDisplay = '';
      let requiredDisplay = '';
      
      if (metric.type === 'number') {
        const rawValue = typeof metric.raw_value === 'number' ? metric.raw_value : (metric.value !== null && typeof metric.value === 'number' ? metric.value : 0);
        valueDisplay = `${rawValue}`;
        const required = (metric.required !== undefined && metric.required !== null) ? metric.required : '不明';
        requiredDisplay = `${required}以上`;
      } else {
        valueDisplay = String(metric.value ?? '-');
        requiredDisplay = '設置あり';
      }
      
      return `
        <tr class="${metric.met ? 'metric-met' : ''}">
          <td>${this.escape(metric.label)}</td>
          <td class="metric-value">${this.escape(valueDisplay)}</td>
          <td class="metric-required">${this.escape(requiredDisplay)}</td>
        </tr>
      `;
    }).join('');
    this.tableBodyEl.innerHTML = rows;
  }

  private renderError(message: string): void {
    if (this.tableBodyEl) {
      this.tableBodyEl.innerHTML = `<tr><td colspan="3" class="error">${this.escape(message)}</td></tr>`;
    }
  }

  private escape(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

document.addEventListener('DOMContentLoaded', () => new DetailPage());