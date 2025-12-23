"use strict";
/**
 * バリアナビ プロフィール画面
 */
class ProfilePage {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.userId = null;
        this.favoriteStations = [];
        this.stationSearchTimeout = null;
        this.init();
    }
    init() {
        this.checkAuthStatus();
        this.setupEventListeners();
        this.loadProfile();
    }
    checkAuthStatus() {
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        const userId = localStorage.getItem('userId');
        if (!isLoggedIn || !userId) {
            window.location.href = 'login.html';
            return;
        }
        this.userId = userId;
    }
    setupEventListeners() {
        // 戻るボタン
        const backBtn = document.getElementById('back-btn');
        backBtn?.addEventListener('click', () => {
            window.location.href = 'home.html';
        });
        // キャンセルボタン
        const cancelBtn = document.getElementById('cancel-btn');
        cancelBtn?.addEventListener('click', () => {
            if (confirm('変更を破棄しますか？')) {
                window.location.href = 'home.html';
            }
        });
        // フォーム送信
        const form = document.getElementById('profile-form');
        form?.addEventListener('submit', (e) => this.handleSubmit(e));
        // 駅検索
        const stationSearchInput = document.getElementById('station-search-input');
        stationSearchInput?.addEventListener('input', (e) => {
            const keyword = e.target.value.trim();
            if (keyword.length >= 2) {
                this.debounceSearch(keyword);
            }
            else {
                this.hideStationSearchResults();
            }
        });
        // 駅検索結果外をクリックしたら閉じる
        document.addEventListener('click', (e) => {
            const results = document.getElementById('station-search-results');
            const input = document.getElementById('station-search-input');
            if (results && input &&
                !results.contains(e.target) &&
                !input.contains(e.target)) {
                this.hideStationSearchResults();
            }
        });
    }
    debounceSearch(keyword) {
        if (this.stationSearchTimeout) {
            clearTimeout(this.stationSearchTimeout);
        }
        this.stationSearchTimeout = window.setTimeout(() => {
            this.searchStations(keyword);
        }, 300);
    }
    async searchStations(keyword) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stations/search?keyword=${encodeURIComponent(keyword)}&limit=10`);
            const data = await response.json();
            if (data.success && data.data) {
                this.showStationSearchResults(data.data);
            }
        }
        catch (error) {
            console.error('Station search error:', error);
        }
    }
    showStationSearchResults(stations) {
        const resultsContainer = document.getElementById('station-search-results');
        if (!resultsContainer)
            return;
        if (stations.length === 0) {
            resultsContainer.innerHTML = '<div class="search-result-item">駅が見つかりませんでした</div>';
            resultsContainer.style.display = 'block';
            return;
        }
        resultsContainer.innerHTML = stations
            .filter(station => !this.favoriteStations.some(fav => fav.id === station.id))
            .map(station => `
        <div class="search-result-item" data-station-id="${station.id}" data-station-name="${this.escapeHtml(station.station_name)}">
          <span class="station-name">${this.escapeHtml(station.station_name)}</span>
          ${station.prefecture ? `<span class="station-location">${this.escapeHtml(station.prefecture)}${station.city ? ` ${this.escapeHtml(station.city)}` : ''}</span>` : ''}
        </div>
      `).join('');
        // クリックイベントを追加
        resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const stationId = parseInt(item.getAttribute('data-station-id') || '0');
                const stationName = item.getAttribute('data-station-name') || '';
                if (stationId && stationName) {
                    this.addFavoriteStation(stationId, stationName);
                    const input = document.getElementById('station-search-input');
                    if (input)
                        input.value = '';
                    this.hideStationSearchResults();
                }
            });
        });
        resultsContainer.style.display = 'block';
    }
    hideStationSearchResults() {
        const resultsContainer = document.getElementById('station-search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
    addFavoriteStation(stationId, stationName) {
        if (this.favoriteStations.some(fav => fav.id === stationId)) {
            return;
        }
        this.favoriteStations.push({ id: stationId, name: stationName });
        this.renderFavoriteStations();
    }
    removeFavoriteStation(stationId) {
        this.favoriteStations = this.favoriteStations.filter(fav => fav.id !== stationId);
        this.renderFavoriteStations();
    }
    renderFavoriteStations() {
        const container = document.getElementById('favorite-stations-list');
        if (!container)
            return;
        if (this.favoriteStations.length === 0) {
            container.innerHTML = '<p class="empty-message">お気に入りの駅が登録されていません</p>';
            return;
        }
        container.innerHTML = this.favoriteStations.map(fav => `
      <div class="favorite-station-item">
        <span class="station-name">${this.escapeHtml(fav.name)}</span>
        <button type="button" class="remove-station-btn" data-station-id="${fav.id}">削除</button>
      </div>
    `).join('');
        // 削除ボタンのイベントを追加
        container.querySelectorAll('.remove-station-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const stationId = parseInt(btn.getAttribute('data-station-id') || '0');
                if (stationId) {
                    this.removeFavoriteStation(stationId);
                }
            });
        });
    }
    async loadProfile() {
        const loadingEl = document.getElementById('loading');
        const formEl = document.getElementById('profile-form');
        const errorEl = document.getElementById('error-message');
        if (!this.userId) {
            if (loadingEl)
                loadingEl.style.display = 'none';
            if (errorEl) {
                errorEl.textContent = 'ユーザーIDが取得できませんでした';
                errorEl.style.display = 'block';
            }
            return;
        }
        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/profile?user_id=${this.userId}`, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            const data = await response.json();
            if (loadingEl)
                loadingEl.style.display = 'none';
            if (data.success && data.data) {
                this.populateForm(data.data);
                if (formEl)
                    formEl.style.display = 'block';
            }
            else {
                // プロフィールが存在しない場合、ユーザー情報のみ表示
                await this.loadUserInfo();
                if (formEl)
                    formEl.style.display = 'block';
            }
        }
        catch (error) {
            console.error('Load profile error:', error);
            if (loadingEl)
                loadingEl.style.display = 'none';
            if (errorEl) {
                errorEl.textContent = 'プロフィールの読み込みに失敗しました';
                errorEl.style.display = 'block';
            }
            // エラーでもフォームは表示
            await this.loadUserInfo();
            if (formEl)
                formEl.style.display = 'block';
        }
    }
    async loadUserInfo() {
        // ユーザー名はlocalStorageから取得
        const username = localStorage.getItem('username') || '';
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.value = username;
        }
        // メールアドレスはlocalStorageから取得
        const email = localStorage.getItem('userEmail') || '';
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.value = email;
        }
    }
    populateForm(data) {
        // 基本情報
        const usernameInput = document.getElementById('username');
        const emailInput = document.getElementById('email');
        if (usernameInput)
            usernameInput.value = data.username || '';
        if (emailInput)
            emailInput.value = data.email || '';
        // 障害情報（最初の1つを選択状態にする）
        if (data.disability_type && Array.isArray(data.disability_type) && data.disability_type.length > 0) {
            const select = document.getElementById('disability_type');
            if (select && data.disability_type[0]) {
                select.value = data.disability_type[0];
            }
        }
        // お気に入りの駅
        if (data.favorite_stations && Array.isArray(data.favorite_stations) && data.favorite_stations.length > 0) {
            // 駅IDから駅名を取得する必要がある
            // 簡易的にIDのみ保存し、読み込み時に駅名を取得
            this.favoriteStations = data.favorite_stations.map(id => ({ id, name: `駅ID: ${id}` }));
            // 駅名を取得して更新
            this.loadFavoriteStationNames(data.favorite_stations);
        }
        else {
            this.favoriteStations = [];
        }
        this.renderFavoriteStations();
        // 優先したい機能
        if (data.preferred_features && Array.isArray(data.preferred_features)) {
            data.preferred_features.forEach(feature => {
                const checkbox = document.querySelector(`input[name="preferred_features"][value="${feature}"]`);
                if (checkbox)
                    checkbox.checked = true;
            });
        }
    }
    async loadFavoriteStationNames(stationIds) {
        // 各駅IDから駅名を取得
        const stations = [];
        for (const id of stationIds) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/stations/${id}`);
                const data = await response.json();
                if (data.success && data.data) {
                    stations.push({ id, name: data.data.station_name });
                }
            }
            catch (error) {
                console.error(`Failed to load station ${id}:`, error);
                stations.push({ id, name: `駅ID: ${id}` });
            }
        }
        this.favoriteStations = stations;
        this.renderFavoriteStations();
    }
    async handleSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        // ユーザー名のバリデーション
        const username = formData.get('username');
        if (!username || username.trim().length === 0) {
            this.showError('ユーザー名を入力してください');
            return;
        }
        // フォームデータを収集
        const disabilitySelect = document.getElementById('disability_type');
        const selectedDisability = disabilitySelect?.value || '';
        const disabilityTypes = selectedDisability ? [selectedDisability] : [];
        const favoriteStationIds = this.favoriteStations.map(fav => fav.id);
        const featureCheckboxes = document.querySelectorAll('input[name="preferred_features"]:checked');
        const preferredFeatures = Array.from(featureCheckboxes).map(cb => cb.value);
        const profileData = {
            username: username.trim(),
            disability_type: disabilityTypes.length > 0 ? disabilityTypes : undefined,
            favorite_stations: favoriteStationIds.length > 0 ? favoriteStationIds : undefined,
            preferred_features: preferredFeatures.length > 0 ? preferredFeatures : undefined,
        };
        // APIに送信
        await this.saveProfile(profileData);
    }
    async saveProfile(data) {
        const saveBtn = document.querySelector('.save-btn');
        const successEl = document.getElementById('save-success');
        if (!this.userId) {
            this.showError('ユーザーIDが取得できませんでした');
            return;
        }
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = '保存中...';
        }
        try {
            const requestData = {
                ...data,
                user_id: parseInt(this.userId),
            };
            const response = await fetch(`${this.apiBaseUrl}/auth/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
            });
            const result = await response.json();
            if (result.success) {
                // ユーザー名が変更された場合、localStorageも更新
                if (data.username) {
                    localStorage.setItem('username', data.username);
                }
                // 保存成功メッセージを表示
                if (successEl) {
                    successEl.textContent = 'プロフィールを保存しました';
                    successEl.style.display = 'block';
                }
                // 1秒後にhome画面にリダイレクト
                setTimeout(() => {
                    window.location.href = 'home.html';
                }, 1000);
            }
            else {
                this.showError(result.error || 'プロフィールの保存に失敗しました');
            }
        }
        catch (error) {
            console.error('Save profile error:', error);
            this.showError('プロフィールの保存に失敗しました');
        }
        finally {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = '保存';
            }
        }
    }
    showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
    }
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new ProfilePage();
});
//# sourceMappingURL=profile.js.map