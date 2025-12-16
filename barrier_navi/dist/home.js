"use strict";
/**
 * バリアナビ ホーム画面
 */
class HomePage {
    constructor() {
        this.init();
    }
    init() {
        this.checkAuthStatus();
        this.setupEventListeners();
    }
    checkAuthStatus() {
        // ログインしていない場合はログイン画面にリダイレクト
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        const isGuest = localStorage.getItem('isGuest') === 'true';
        if (!isLoggedIn && !isGuest) {
            window.location.href = 'login.html';
        }
    }
    setupEventListeners() {
        const profileBtn = document.getElementById('profile-btn');
        profileBtn?.addEventListener('click', () => {
            this.showProfileMenu();
        });
    }
    showProfileMenu() {
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
        const closeMenu = (e) => {
            if (e.key === 'Escape') {
                menu.remove();
                document.removeEventListener('keydown', closeMenu);
            }
        };
        document.addEventListener('keydown', closeMenu);
    }
    handleLogout() {
        if (confirm('ログアウトしますか？')) {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('isGuest');
            localStorage.removeItem('username');
            localStorage.removeItem('rememberMe');
            window.location.href = 'login.html';
        }
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
    new HomePage();
});
//# sourceMappingURL=home.js.map