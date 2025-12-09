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
        const weights = params.get('weights');
        const query = new URLSearchParams();
        if (weights)
            query.set('weights', weights);
        const response = await this.fetchApi(`/body/stations/${stationId}?${query.toString()}`);
        if (response.success && response.data) {
            this.renderDetail(response.data);
        }
        else {
            this.renderError((response === null || response === void 0 ? void 0 : response.error) || 'データを取得できませんでした。');
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
        var _a, _b, _c, _d;
        if (!this.titleEl || !this.scoreEl || !this.metaEl || !this.tableBodyEl)
            return;
        this.titleEl.textContent = detail.station_name;
        this.scoreEl.textContent = `${detail.score.label}（${detail.score.percentage}%）`;
        const city = detail.city ? ` ${detail.city}` : '';
        this.metaEl.innerHTML = `
      <p>鉄道事業者: ${this.escape(detail.operator)}</p>
      <p>路線: ${this.escape(detail.line_name)}</p>
      <p>所在地: ${this.escape(detail.prefecture)}${this.escape(city)}</p>
    `;
        const rows = detail.metrics
            .map((metric) => {
            return `
        <tr class="${metric.met ? 'metric-met' : ''}">
          <td>${this.escape(metric.label)}</td>
          <td class="metric-value">${(_a = metric.value) !== null && _a !== void 0 ? _a : '-'}</td>
        </tr>
      `;
        })
            .join('');
        this.tableBodyEl.innerHTML = rows;
    }
    renderError(message) {
        if (this.tableBodyEl) {
            this.tableBodyEl.innerHTML = `<tr><td colspan="2" class="error">${this.escape(message)}</td></tr>`;
        }
    }
    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
document.addEventListener('DOMContentLoaded', () => new DetailPage());

