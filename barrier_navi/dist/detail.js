"use strict";
class DetailPage {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.titleEl = null;
        this.scoreEl = null;
        this.metaEl = null;
        this.tableBodyEl = null;
        this.titleEl = document.getElementById('detail-title');
        this.scoreEl = document.getElementById('detail-score');
        this.metaEl = document.getElementById('detail-meta');
        this.tableBodyEl = document.getElementById('detail-table-body');
        this.load();
    }
    async load() {
        const params = new URLSearchParams(window.location.search);
        const stationId = Number(params.get('stationId'));
        if (!stationId) {
            this.renderError('駅IDが指定されていません。');
            return;
        }
        const response = await this.fetchApi(`/body/stations/${stationId}`);
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
<<<<<<< HEAD
=======
        var _a;
>>>>>>> 648b75248cbef8bc9a756f694c33a9b32ce968b7
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
<<<<<<< HEAD
        const rows = detail.metrics.map((metric) => {
            return `
        <tr class="${metric.met ? 'metric-met' : ''}">
          <td>${this.escape(metric.label)}</td>
          <td class="metric-value">${metric.value ?? '-'}</td>
=======
        // デバッグ用：APIレスポンス全体を確認
        console.log('Detail data:', detail);
        console.log('Metrics:', detail.metrics);
        const rows = detail.metrics.map((metric) => {
            // 値の表示
            let valueDisplay = '';
            let requiredDisplay = '';
            // デバッグ用：各metricオブジェクトを確認
            console.log('Metric:', metric, 'required:', metric.required);
            if (metric.type === 'number') {
                // 数値型：実際の値を表示
                const rawValue = typeof metric.raw_value === 'number' ? metric.raw_value : (metric.value !== null && typeof metric.value === 'number' ? metric.value : 0);
                valueDisplay = `${rawValue}`;
                // requiredが存在するかチェック（APIレスポンスに含まれているか確認）
                const required = (metric.required !== undefined && metric.required !== null) ? metric.required : '不明';
                requiredDisplay = `${required}以上`;
            }
            else {
                // フラグ型：○/×を表示
                valueDisplay = String((_a = metric.value) !== null && _a !== void 0 ? _a : '-');
                requiredDisplay = '設置あり';
            }
            return `
        <tr class="${metric.met ? 'metric-met' : ''}">
          <td>${this.escape(metric.label)}</td>
          <td class="metric-value">${this.escape(valueDisplay)}</td>
          <td class="metric-required">${this.escape(requiredDisplay)}</td>
>>>>>>> 648b75248cbef8bc9a756f694c33a9b32ce968b7
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
<<<<<<< HEAD
//# sourceMappingURL=detail.js.map
=======
>>>>>>> 648b75248cbef8bc9a756f694c33a9b32ce968b7
