/**
 * バリアナビ プロフィール画面
 */

interface ProfileData {
  username: string;
  email: string;
  disability_type?: string[];
  favorite_stations?: number[];  // APIからは駅IDの配列が返される（保存時も駅IDの配列を送信）
  preferred_features?: string[];
}

interface Station {
  id: number;
  station_name: string;
  prefecture?: string;
  city?: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

class ProfilePage {
  private apiBaseUrl = 'http://localhost:5000/api';
  private userId: string | null = null;
  private favoriteStations: Array<{ id: number; name: string }> = [];
  private stationSearchTimeout: number | null = null;

  constructor() {
    this.init();
  }

  private init(): void {
    this.checkAuthStatus();
    this.setupEventListeners();
    this.loadProfile();
  }

  private checkAuthStatus(): void {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const userId = localStorage.getItem('userId');
    
    if (!isLoggedIn || !userId) {
      window.location.href = 'login.html';
      return;
    }
    
    this.userId = userId;
  }

  private setupEventListeners(): void {
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
    const form = document.getElementById('profile-form') as HTMLFormElement;
    form?.addEventListener('submit', (e) => this.handleSubmit(e));

    // 駅検索
    const stationSearchInput = document.getElementById('station-search-input') as HTMLInputElement;
    stationSearchInput?.addEventListener('input', (e) => {
      const keyword = (e.target as HTMLInputElement).value.trim();
      if (keyword.length >= 2) {
        this.debounceSearch(keyword);
      } else {
        this.hideStationSearchResults();
      }
    });

    // 駅検索結果外をクリックしたら閉じる
    document.addEventListener('click', (e) => {
      const results = document.getElementById('station-search-results');
      const input = document.getElementById('station-search-input');
      if (results && input && 
          !results.contains(e.target as Node) && 
          !input.contains(e.target as Node)) {
        this.hideStationSearchResults();
      }
    });

    // お気に入り駅の削除ボタン（イベント委譲を使用）
    const favoriteStationsList = document.getElementById('favorite-stations-list');
    favoriteStationsList?.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('remove-station-btn')) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = target as HTMLButtonElement;
        const stationIdAttr = btn.getAttribute('data-station-id');
        const stationIndexAttr = btn.getAttribute('data-station-index');
        const stationId = stationIdAttr ? parseInt(stationIdAttr) : 0;
        const stationIndex = stationIndexAttr ? parseInt(stationIndexAttr) : -1;
        
        console.log('Delete button clicked (delegated), stationId:', stationId, 'index:', stationIndex);
        
        // インデックスが有効な場合は、インデックスで削除（最も確実）
        if (!isNaN(stationIndex) && stationIndex >= 0 && stationIndex < this.favoriteStations.length) {
          console.log('Removing station by index:', stationIndex);
          this.favoriteStations.splice(stationIndex, 1);
          this.renderFavoriteStations();
          return;
        }
        
        // 駅IDが有効な場合は、IDで削除
        if (!isNaN(stationId) && stationId > 0) {
          console.log('Removing station by ID:', stationId);
          this.removeFavoriteStation(stationId);
          return;
        }
        
        // 駅名で削除を試みる（フォールバック）
        const stationItem = btn.closest('.favorite-station-item');
        if (stationItem) {
          let stationName = stationItem.querySelector('.station-name')?.textContent || '';
          stationName = stationName.replace(/^駅ID:\s*/, '').trim();
          console.log('Removing station by name:', stationName);
          if (stationName) {
            this.removeFavoriteStationByName(stationName);
          }
        }
      }
    });

  }

  private debounceSearch(keyword: string): void {
    if (this.stationSearchTimeout) {
      clearTimeout(this.stationSearchTimeout);
    }
    this.stationSearchTimeout = window.setTimeout(() => {
      this.searchStations(keyword);
    }, 300);
  }

  private async searchStations(keyword: string): Promise<void> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/stations/search?keyword=${encodeURIComponent(keyword)}&limit=10`);
      const data: ApiResponse<Station[]> = await response.json();

      if (data.success && data.data) {
        this.showStationSearchResults(data.data);
      }
    } catch (error) {
      console.error('Station search error:', error);
    }
  }

  private showStationSearchResults(stations: Station[]): void {
    const resultsContainer = document.getElementById('station-search-results');
    if (!resultsContainer) return;

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
          const input = document.getElementById('station-search-input') as HTMLInputElement;
          if (input) input.value = '';
          this.hideStationSearchResults();
        }
      });
    });

    resultsContainer.style.display = 'block';
  }

  private hideStationSearchResults(): void {
    const resultsContainer = document.getElementById('station-search-results');
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
    }
  }

  private addFavoriteStation(stationId: number, stationName: string): void {
    if (this.favoriteStations.some(fav => fav.id === stationId)) {
      return;
    }

    this.favoriteStations.push({ id: stationId, name: stationName });
    this.renderFavoriteStations();
  }

  private removeFavoriteStation(stationId: number): void {
    console.log('Before remove:', this.favoriteStations.length);
    this.favoriteStations = this.favoriteStations.filter(fav => fav.id !== stationId);
    console.log('After remove:', this.favoriteStations.length);
    this.renderFavoriteStations();
  }

  private removeFavoriteStationByName(stationName: string): void {
    console.log('Before remove by name:', this.favoriteStations.length, 'name:', stationName);
    // 駅名が「駅ID: X」の形式の場合も考慮して削除
    const cleanStationName = stationName.replace(/^駅ID:\s*/, '').trim();
    this.favoriteStations = this.favoriteStations.filter(fav => {
      const cleanFavName = fav.name.replace(/^駅ID:\s*/, '').trim();
      return cleanFavName !== cleanStationName && fav.name !== stationName;
    });
    console.log('After remove by name:', this.favoriteStations.length);
    this.renderFavoriteStations();
  }

  private renderFavoriteStations(): void {
    const container = document.getElementById('favorite-stations-list');
    if (!container) return;

    if (this.favoriteStations.length === 0) {
      container.innerHTML = '<p class="empty-message">お気に入りの駅が登録されていません</p>';
      return;
    }

    container.innerHTML = this.favoriteStations.map((fav, index) => `
      <div class="favorite-station-item" data-station-index="${index}">
        <span class="station-name">${this.escapeHtml(fav.name)}</span>
        <button type="button" class="remove-station-btn" data-station-id="${fav.id}" data-station-index="${index}">削除</button>
      </div>
    `).join('');

    // イベント委譲を使用しているため、ここで個別にイベントハンドラーを追加する必要はない
    // setupEventListeners()で設定済み
  }

  private async loadProfile(): Promise<void> {
    const loadingEl = document.getElementById('loading');
    const formEl = document.getElementById('profile-form') as HTMLElement;
    const errorEl = document.getElementById('error-message');

    if (!this.userId) {
      if (loadingEl) loadingEl.style.display = 'none';
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

      const data: ApiResponse<ProfileData> = await response.json();

      if (loadingEl) loadingEl.style.display = 'none';

      if (data.success && data.data) {
        this.populateForm(data.data);
        if (formEl) formEl.style.display = 'block';
      } else {
        // プロフィールが存在しない場合、ユーザー情報のみ表示
        await this.loadUserInfo();
        if (formEl) formEl.style.display = 'block';
      }
    } catch (error) {
      console.error('Load profile error:', error);
      if (loadingEl) loadingEl.style.display = 'none';
      if (errorEl) {
        errorEl.textContent = 'プロフィールの読み込みに失敗しました';
        errorEl.style.display = 'block';
      }
      // エラーでもフォームは表示
      await this.loadUserInfo();
      if (formEl) formEl.style.display = 'block';
    }
  }

  private async loadUserInfo(): Promise<void> {
    // ユーザー名はlocalStorageから取得
    const username = localStorage.getItem('username') || '';
    const usernameInput = document.getElementById('username') as HTMLInputElement;
    if (usernameInput) {
      usernameInput.value = username;
    }

    // メールアドレスはlocalStorageから取得
    const email = localStorage.getItem('userEmail') || '';
    const emailInput = document.getElementById('email') as HTMLInputElement;
    if (emailInput) {
      emailInput.value = email;
    }
  }

  private populateForm(data: ProfileData): void {
    // 基本情報
    const usernameInput = document.getElementById('username') as HTMLInputElement;
    const emailInput = document.getElementById('email') as HTMLInputElement;

    if (usernameInput) usernameInput.value = data.username || '';
    if (emailInput) emailInput.value = data.email || '';

    // 障害情報（最初の1つを選択状態にする）
    if (data.disability_type && Array.isArray(data.disability_type) && data.disability_type.length > 0) {
      const select = document.getElementById('disability_type') as HTMLSelectElement;
      if (select && data.disability_type[0]) {
        select.value = data.disability_type[0];
      }
    }

    // お気に入りの駅（APIからは駅IDの配列が返される）
    if (data.favorite_stations && Array.isArray(data.favorite_stations) && data.favorite_stations.length > 0) {
      // APIから駅IDの配列が返されるので、駅IDから駅名を取得して表示用に使用
      const stationIds = data.favorite_stations.map(id => parseInt(String(id))).filter(id => !isNaN(id) && id > 0);
      if (stationIds.length > 0) {
        this.loadFavoriteStationNamesFromIds(stationIds);
      } else {
        this.favoriteStations = [];
        this.renderFavoriteStations();
      }
    } else {
      this.favoriteStations = [];
      this.renderFavoriteStations();
    }

    // 優先したい機能
    if (data.preferred_features && Array.isArray(data.preferred_features)) {
      data.preferred_features.forEach(feature => {
        const checkbox = document.querySelector(`input[name="preferred_features"][value="${feature}"]`) as HTMLInputElement;
        if (checkbox) checkbox.checked = true;
      });
    }
  }

  private async loadFavoriteStationNamesFromIds(stationIds: number[]): Promise<void> {
    // 各駅IDから駅名を取得
    const stations: Array<{ id: number; name: string }> = [];
    for (const id of stationIds) {
      try {
        const response = await fetch(`${this.apiBaseUrl}/stations/${id}`);
        const data: ApiResponse<Station> = await response.json();
        if (data.success && data.data) {
          stations.push({ id: data.data.id, name: data.data.station_name });
        } else {
          console.warn(`Station not found: ${id}`);
          stations.push({ id, name: `駅ID: ${id}` });
        }
      } catch (error) {
        console.error(`Failed to load station ${id}:`, error);
        stations.push({ id, name: `駅ID: ${id}` });
      }
    }
    this.favoriteStations = stations;
    this.renderFavoriteStations();
  }

  private async loadFavoriteStationNamesFromNames(stationNames: string[]): Promise<void> {
    // 各駅名から駅IDを取得（完全一致で検索）
    const stations: Array<{ id: number; name: string }> = [];
    for (const name of stationNames) {
      // 「駅ID: X」の形式の場合は除去して駅名のみを使用
      const cleanName = name.replace(/^駅ID:\s*/, '').trim();
      
      // 駅名から駅IDを検索（完全一致）
      try {
        const response = await fetch(`${this.apiBaseUrl}/stations/search?keyword=${encodeURIComponent(cleanName)}&limit=50`);
        const data: ApiResponse<Station[]> = await response.json();
        if (data.success && data.data && data.data.length > 0) {
          // 完全一致する駅を探す
          const exactMatch = data.data.find(station => station.station_name === cleanName);
          if (exactMatch) {
            stations.push({ id: exactMatch.id, name: exactMatch.station_name });
          } else {
            // 完全一致が見つからない場合は最初の1件を使用
            stations.push({ id: data.data[0].id, name: data.data[0].station_name });
          }
        } else {
          // 見つからない場合は駅名のみを使用（IDは0、「駅ID:」プレフィックスなしで表示）
          console.warn(`Station not found: ${cleanName}`);
          stations.push({ id: 0, name: cleanName });
        }
      } catch (error) {
        console.error(`Failed to load station ${cleanName}:`, error);
        stations.push({ id: 0, name: cleanName });
      }
    }
    this.favoriteStations = stations;
    this.renderFavoriteStations();
  }

  private async handleSubmit(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);

    // ユーザー名のバリデーション
    const username = formData.get('username') as string;
    if (!username || username.trim().length === 0) {
      this.showError('ユーザー名を入力してください');
      return;
    }

    // フォームデータを収集
    const disabilitySelect = document.getElementById('disability_type') as HTMLSelectElement;
    const selectedDisability = disabilitySelect?.value || '';
    const disabilityTypes = selectedDisability ? [selectedDisability] : [];

    // 駅IDが0のもの（駅名からIDを取得できなかったもの）を除外
    const favoriteStationIds = this.favoriteStations
      .map(fav => fav.id)
      .filter(id => id > 0);

    const featureCheckboxes = document.querySelectorAll<HTMLInputElement>('input[name="preferred_features"]:checked');
    const preferredFeatures = Array.from(featureCheckboxes).map(cb => cb.value);

    const profileData: Partial<ProfileData> = {
      username: username.trim(),
      disability_type: disabilityTypes.length > 0 ? disabilityTypes : [],
      favorite_stations: favoriteStationIds, // 空の配列でも明示的に送信（削除を反映するため）
      preferred_features: preferredFeatures, // 空の配列でも明示的に送信（全てのチェックを外した場合に対応）
    };

    // APIに送信
    await this.saveProfile(profileData);
  }

  private async saveProfile(data: Partial<ProfileData>): Promise<void> {
    const saveBtn = document.querySelector('.save-btn') as HTMLButtonElement;
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

      const result: ApiResponse<ProfileData> = await response.json();

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
      } else {
        this.showError(result.error || 'プロフィールの保存に失敗しました');
      }
    } catch (error) {
      console.error('Save profile error:', error);
      this.showError('プロフィールの保存に失敗しました');
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = '保存';
      }
    }
  }

  private showError(message: string): void {
    const errorEl = document.getElementById('error-message');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      setTimeout(() => {
        errorEl.style.display = 'none';
      }, 5000);
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

}

document.addEventListener('DOMContentLoaded', () => {
  new ProfilePage();
});

