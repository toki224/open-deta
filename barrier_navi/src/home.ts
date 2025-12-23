/**
 * バリアナビ ホーム画面
 */

class HomePage {
  constructor() {
    this.init();
  }

  private init(): void {
    this.checkAuthStatus();
    this.setupEventListeners();
  }

  private checkAuthStatus(): void {
    // ログインしていない場合はログイン画面にリダイレクト
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const isGuest = localStorage.getItem('isGuest') === 'true';
    
    if (!isLoggedIn && !isGuest) {
      window.location.href = 'login.html';
    }
  }

  private setupEventListeners(): void {
    const profileBtn = document.getElementById('profile-btn');
    profileBtn?.addEventListener('click', () => {
      this.showProfileMenu();
    });
  }

  private showProfileMenu(): void {
    const username = localStorage.getItem('username') || 'ユーザー';
    const isGuest = localStorage.getItem('isGuest') === 'true';
    
    const menu = document.createElement('div');
    menu.className = 'profile-menu';
    menu.innerHTML = `
      <div class="profile-menu-content">
        <div class="profile-menu-header">
          <p class="profile-menu-username">${this.escapeHtml(username)}</p>
          ${isGuest ? '<p class="profile-menu-guest">ゲストモード</p>' : ''}
        </div>
        <div class="profile-menu-divider"></div>
        ${!isGuest ? `
        <button class="profile-menu-item" id="profile-menu-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <span>プロフィール</span>
        </button>
        ` : ''}
        <button class="profile-menu-item" id="logout-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          <span>ログアウト</span>
        </button>
      </div>
    `;
    
    // 既存のメニューを削除
    const existingMenu = document.querySelector('.profile-menu');
    if (existingMenu) {
      existingMenu.remove();
    }
    
    document.body.appendChild(menu);
    
    // プロフィールボタンのイベント（ゲストでない場合のみ）
    if (!isGuest) {
      const profileMenuBtn = document.getElementById('profile-menu-btn');
      profileMenuBtn?.addEventListener('click', () => {
        this.handleProfile();
        menu.remove();
      });
    }
    
    // ログアウトボタンのイベント
    const logoutBtn = document.getElementById('logout-btn');
    logoutBtn?.addEventListener('click', () => {
      this.handleLogout();
    });
    
    // メニュー外をクリックしたら閉じる
    menu.addEventListener('click', (e) => {
      if (e.target === menu) {
        menu.remove();
      }
    });
    
    // ESCキーで閉じる
    const closeMenu = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        menu.remove();
        document.removeEventListener('keydown', closeMenu);
      }
    };
    document.addEventListener('keydown', closeMenu);
  }

  private handleProfile(): void {
    // プロフィール画面への遷移
    window.location.href = 'profile.html';
  }

  private handleLogout(): void {
    if (confirm('ログアウトしますか？')) {
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('isGuest');
      localStorage.removeItem('username');
      localStorage.removeItem('rememberMe');
      localStorage.removeItem('userId');
      window.location.href = 'login.html';
    }
  }

  private escapeHtml(text: string | null | undefined): string {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new HomePage();
});

