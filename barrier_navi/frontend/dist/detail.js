"use strict";
class DetailPage {
    constructor() {
        this.apiBaseUrl = '/api';
        this.titleEl = null;
        this.scoreEl = null;
        this.metaEl = null;
        this.tableBodyEl = null;
        // ★追加: 現在のモード
        this.currentMode = 'body';
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
        }
        else if (urlMode === 'vision' || bodyMode === 'vision') {
            this.currentMode = 'vision';
        }
        else {
            this.currentMode = 'body';
        }
        this.setupBackButton();
        this.load();
    }
    setupBackButton() {
        const backBtn = document.getElementById('back_btn');
        if (backBtn) {
            if (this.currentMode === 'hearing') {
                backBtn.href = '/hearing';
            }
            else if (this.currentMode === 'vision') {
                backBtn.href = '/vision';
            }
            else {
                backBtn.href = '/index';
            }
        }
    }
    async load() {
        const params = new URLSearchParams(window.location.search);
        const stationId = Number(params.get('stationId'));
        if (!stationId) {
            this.renderError('駅IDが指定されていません。');
            return;
        }
        // ★修正: モードに応じてAPIパスを切り替える
        const apiPath = this.currentMode === 'hearing' ? '/hearing/stations' : this.currentMode === 'vision' ? '/vision/stations' : '/body/stations';
        // 修正後:
        const response = await this.fetchApi(`${apiPath}/${stationId}`);
        if (response.success && response.data) {
            this.renderDetail(response.data);
        }
        else {
            this.renderError(response.error || 'データを取得できませんでした。');
        }
    }
    async fetchApi(endpoint) {
        try {
            const res = await fetch(`${this.apiBaseUrl}${endpoint}`);
            return await res.json();
        }
        catch (error) {
            return { success: false, error: String(error) };
        }
    }
    renderDetail(detail) {
        if (!this.titleEl || !this.scoreEl || !this.metaEl || !this.tableBodyEl)
            return;
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
            if (metric.type === 'ratio') {
                // 割合型: 既にAPI側で「何分の何 (何%)」形式で処理されているので、そのまま表示
                valueDisplay = String(metric.value ?? '-');
                const requiredPercent = (metric.required !== undefined && metric.required !== null) ? (metric.required * 100) : 100;
                requiredDisplay = `${requiredPercent}%以上`;
            }
            else if (metric.type === 'number') {
                const rawValue = typeof metric.raw_value === 'number' ? metric.raw_value : (metric.value !== null && typeof metric.value === 'number' ? metric.value : 0);
                valueDisplay = `${rawValue}`;
                const required = (metric.required !== undefined && metric.required !== null) ? metric.required : '不明';
                requiredDisplay = `${required}以上`;
            }
            else {
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
    renderError(message) {
        if (this.tableBodyEl) {
            this.tableBodyEl.innerHTML = `<tr><td colspan="3" class="error">${this.escape(message)}</td></tr>`;
        }
    }
    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
document.addEventListener('DOMContentLoaded', () => new DetailPage());
//# sourceMappingURL=detail.js.map