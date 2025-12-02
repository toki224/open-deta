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
  required: number;
  ratio: number;
  met: boolean;
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

  constructor() {
    this.titleEl = document.getElementById('detail-title');
    this.scoreEl = document.getElementById('detail-score');
    this.metaEl = document.getElementById('detail-meta');
    this.tableBodyEl = document.getElementById('detail-table-body');
    this.load();
  }

  private async load(): Promise<void> {
    const params = new URLSearchParams(window.location.search);
    const stationId = Number(params.get('stationId'));
    if (!stationId) {
      this.renderError('駅IDが指定されていません。');
      return;
    }

    const weights = params.get('weights');
    const query = new URLSearchParams();
    if (weights) query.set('weights', weights);

    const response = await this.fetchApi<DetailStation>(`/body/stations/${stationId}?${query.toString()}`);
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
    this.scoreEl.textContent = `${detail.score.label}（${detail.score.percentage}%）`;
    const city = detail.city ? ` ${detail.city}` : '';
    this.metaEl.innerHTML = `
      <p>鉄道事業者: ${this.escape(detail.operator)}</p>
      <p>路線: ${this.escape(detail.line_name)}</p>
      <p>所在地: ${this.escape(detail.prefecture)}${this.escape(city)}</p>
    `;

    const rows = detail.metrics.map((metric) => {
      const ratioPercent = Math.round(metric.ratio * 100);
      return `
        <tr class="${metric.met ? 'metric-met' : ''}">
          <td>${this.escape(metric.label)}</td>
          <td class="metric-value">${metric.value ?? '-'}</td>
          <td class="metric-required">${metric.required}</td>
          <td class="metric-ratio">${ratioPercent}%</td>
        </tr>
      `;
    }).join('');
    this.tableBodyEl.innerHTML = rows;
  }

  private renderError(message: string): void {
    if (this.tableBodyEl) {
      this.tableBodyEl.innerHTML = `<tr><td colspan="4" class="error">${this.escape(message)}</td></tr>`;
    }
  }

  private escape(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

document.addEventListener('DOMContentLoaded', () => new DetailPage());

