/**
 * バリナビ ログイン画面
 */

class LoginPage {
  private apiBaseUrl = 'http://localhost:5000/api';

  constructor() {
    this.init();
  }

  private init(): void {
    this.setupEventListeners();
    this.checkAuthStatus();
  }

  private checkAuthStatus(): void {
    // URLパラメータに ?force=true がない場合のみ、既にログインしている場合はホーム画面にリダイレクト
    const urlParams = new URLSearchParams(window.location.search);
    const force = urlParams.get('force') === 'true';
    
    if (!force) {
      const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      const isGuest = localStorage.getItem('isGuest') === 'true';
      
      if (isLoggedIn || isGuest) {
        window.location.href = 'view/home.html';
      }
    }
  }

  private setupEventListeners(): void {
    // ログインフォーム
    const loginForm = document.getElementById('login-form') as HTMLFormElement;
    loginForm?.addEventListener('submit', (e) => this.handleLogin(e));

    // 新規作成ボタン
    const signupBtn = document.getElementById('signup-btn');
    signupBtn?.addEventListener('click', () => this.showSignupModal());

    // ゲストで参加ボタン
    const guestBtn = document.getElementById('guest-btn');
    guestBtn?.addEventListener('click', () => this.handleGuestLogin());

    // パスワードを忘れた場合のリンク
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    forgotPasswordLink?.addEventListener('click', (e) => {
      e.preventDefault();
      this.showResetPasswordModal();
    });

    // 新規作成モーダル
    const signupModal = document.getElementById('signup-modal');
    const closeSignupModal = document.getElementById('close-signup-modal');
    closeSignupModal?.addEventListener('click', () => this.hideSignupModal());
    signupModal?.addEventListener('click', (e) => {
      if (e.target === signupModal) {
        this.hideSignupModal();
      }
    });

    // 新規作成フォーム
    const signupForm = document.getElementById('signup-form') as HTMLFormElement;
    signupForm?.addEventListener('submit', (e) => this.handleSignup(e));

    // パスワードリセットモーダル
    const resetModal = document.getElementById('reset-password-modal');
    const closeResetModal = document.getElementById('close-reset-modal');
    closeResetModal?.addEventListener('click', () => this.hideResetPasswordModal());
    resetModal?.addEventListener('click', (e) => {
      if (e.target === resetModal) {
        this.hideResetPasswordModal();
      }
    });

    // パスワードリセットフォーム
    const resetForm = document.getElementById('reset-password-form') as HTMLFormElement;
    resetForm?.addEventListener('submit', (e) => this.handlePasswordReset(e));
  }

  private async handleLogin(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const username = formData.get('username') as string;
    const password = formData.get('password') as string;

    const errorMessage = document.getElementById('error-message');
    if (errorMessage) {
      errorMessage.style.display = 'none';
      errorMessage.textContent = '';
    }

    try {
      // 実際のAPI呼び出し（バックエンドが実装されていない場合は、ローカルストレージでシミュレート）
      const response = await this.loginUser(username, password);
      
      if (response.success) {
        // ログイン成功
        localStorage.setItem('isLoggedIn', 'true');
        const displayName = response.user?.username || username;
        localStorage.setItem('username', displayName);
        if (response.user?.id) {
          localStorage.setItem('userId', response.user.id.toString());
        }
        if (response.user?.email) {
          localStorage.setItem('userEmail', response.user.email);
        }
        window.location.href = 'view/home.html';
      } else {
        // ログイン失敗
        this.showError(errorMessage, response.error || 'ログインに失敗しました');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showError(errorMessage, 'ログイン処理中にエラーが発生しました');
    }
  }

  private async loginUser(username: string, password: string): Promise<{ success: boolean; error?: string; user?: any }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        return { success: true, user: data.data };
      } else {
        return { success: false, error: data.error || 'ログインに失敗しました' };
      }
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        return { success: false, error: 'APIサーバーに接続できません。サーバーが起動しているか確認してください。' };
      }
      return { success: false, error: 'ログイン処理中にエラーが発生しました' };
    }
  }

  private handleGuestLogin(): void {
    localStorage.setItem('isGuest', 'true');
    localStorage.setItem('username', 'ゲスト');
    window.location.href = 'view/home.html';
  }

  private showSignupModal(): void {
    const modal = document.getElementById('signup-modal');
    if (modal) {
      modal.style.display = 'flex';
    }
  }

  private hideSignupModal(): void {
    const modal = document.getElementById('signup-modal');
    if (modal) {
      modal.style.display = 'none';
      const form = document.getElementById('signup-form') as HTMLFormElement;
      form?.reset();
      const errorMsg = document.getElementById('signup-error-message');
      if (errorMsg) {
        errorMsg.style.display = 'none';
      }
    }
  }

  private async handleSignup(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const username = formData.get('username') as string;
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    const passwordConfirm = formData.get('password-confirm') as string;

    const errorMessage = document.getElementById('signup-error-message');
    if (errorMessage) {
      errorMessage.style.display = 'none';
      errorMessage.textContent = '';
    }

    // バリデーション
    if (!username || !email || !password || !passwordConfirm) {
      this.showError(errorMessage, 'すべての項目を入力してください');
      return;
    }

    if (password !== passwordConfirm) {
      this.showError(errorMessage, 'パスワードが一致しません');
      return;
    }

    if (password.length < 8) {
      this.showError(errorMessage, 'パスワードは8文字以上で入力してください');
      return;
    }

    try {
      const response = await this.createUser(username, email, password);
      
      if (response.success) {
        // アカウント作成成功
        alert('アカウントが作成されました。ログインしてください。');
        this.hideSignupModal();
        // ログインフォームにユーザー名を設定
        const loginUsername = document.getElementById('username') as HTMLInputElement;
        if (loginUsername) {
          loginUsername.value = username;
        }
      } else {
        this.showError(errorMessage, response.error || 'アカウント作成に失敗しました');
      }
    } catch (error) {
      console.error('Signup error:', error);
      this.showError(errorMessage, 'アカウント作成処理中にエラーが発生しました');
    }
  }

  private async createUser(username: string, email: string, password: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });

      // レスポンスがJSONでない場合の処理
      let data;
      try {
        data = await response.json();
      } catch (e) {
        const text = await response.text();
        console.error('JSON parse error:', text);
        return { success: false, error: `サーバーエラー: ${response.status} ${response.statusText}` };
      }

      if (response.ok && data.success) {
        return { success: true };
      } else {
        const errorMsg = data.error || data.message || 'アカウント作成に失敗しました';
        console.error('Signup API error:', errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (error) {
      console.error('Signup network error:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        return { success: false, error: 'APIサーバーに接続できません。サーバーが起動しているか確認してください。' };
      }
      return { success: false, error: `アカウント作成処理中にエラーが発生しました: ${errorMessage}` };
    }
  }

  private showResetPasswordModal(): void {
    const modal = document.getElementById('reset-password-modal');
    if (modal) {
      modal.style.display = 'flex';
    }
  }

  private hideResetPasswordModal(): void {
    const modal = document.getElementById('reset-password-modal');
    if (modal) {
      modal.style.display = 'none';
      const form = document.getElementById('reset-password-form') as HTMLFormElement;
      form?.reset();
      const errorMsg = document.getElementById('reset-error-message');
      const successMsg = document.getElementById('reset-success-message');
      if (errorMsg) {
        errorMsg.style.display = 'none';
      }
      if (successMsg) {
        successMsg.style.display = 'none';
      }
    }
  }

  private async handlePasswordReset(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const email = formData.get('email') as string;

    const errorMessage = document.getElementById('reset-error-message');
    const successMessage = document.getElementById('reset-success-message');
    
    if (errorMessage) {
      errorMessage.style.display = 'none';
      errorMessage.textContent = '';
    }
    if (successMessage) {
      successMessage.style.display = 'none';
      successMessage.textContent = '';
    }

    try {
      const response = await this.resetPassword(email);
      
      if (response.success) {
        if (successMessage) {
          successMessage.textContent = 'パスワードリセット用のリンクをメールアドレスに送信しました。';
          successMessage.style.display = 'block';
        }
        // 3秒後にモーダルを閉じる
        setTimeout(() => {
          this.hideResetPasswordModal();
        }, 3000);
      } else {
        this.showError(errorMessage, response.error || 'パスワードリセットに失敗しました');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      this.showError(errorMessage, 'パスワードリセット処理中にエラーが発生しました');
    }
  }

  private async resetPassword(email: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        return { success: true };
      } else {
        return { success: false, error: data.error || 'パスワードリセットに失敗しました' };
      }
    } catch (error) {
      console.error('Password reset error:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        return { success: false, error: 'APIサーバーに接続できません。サーバーが起動しているか確認してください。' };
      }
      return { success: false, error: 'パスワードリセット処理中にエラーが発生しました' };
    }
  }

  private showError(element: HTMLElement | null, message: string): void {
    if (element) {
      element.textContent = message;
      element.style.display = 'block';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new LoginPage();
});

