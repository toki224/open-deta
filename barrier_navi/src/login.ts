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
        window.location.href = 'home.html';
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
    const rememberMe = (formData.get('remember-me') as string) === 'on';

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
        localStorage.setItem('username', username);
        if (rememberMe) {
          localStorage.setItem('rememberMe', 'true');
        }
        window.location.href = 'home.html';
      } else {
        // ログイン失敗
        this.showError(errorMessage, response.error || 'ログインに失敗しました');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showError(errorMessage, 'ログイン処理中にエラーが発生しました');
    }
  }

  private async loginUser(username: string, password: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        return { success: true };
      } else {
        const data = await response.json();
        return { success: false, error: data.error || 'ログインに失敗しました' };
      }
    } catch (error) {
      // APIが利用できない場合は、デモ用にローカルストレージでシミュレート
      console.warn('API not available, using demo mode');
      return this.demoLogin(username, password);
    }
  }

  private demoLogin(username: string, password: string): { success: boolean; error?: string } {
    // デモ用の簡易ログイン（実際の実装では削除）
    const storedUsers = JSON.parse(localStorage.getItem('demoUsers') || '{}');
    
    if (storedUsers[username] && storedUsers[username].password === password) {
      return { success: true };
    }
    
    // デフォルトのテストユーザー
    if (username === 'test' && password === 'test1234') {
      return { success: true };
    }
    
    return { success: false, error: 'ユーザー名またはパスワードが正しくありません' };
  }

  private handleGuestLogin(): void {
    localStorage.setItem('isGuest', 'true');
    localStorage.setItem('username', 'ゲスト');
    window.location.href = 'home.html';
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

      if (response.ok) {
        return { success: true };
      } else {
        const data = await response.json();
        return { success: false, error: data.error || 'アカウント作成に失敗しました' };
      }
    } catch (error) {
      // APIが利用できない場合は、デモ用にローカルストレージでシミュレート
      console.warn('API not available, using demo mode');
      return this.demoSignup(username, email, password);
    }
  }

  private demoSignup(username: string, email: string, password: string): { success: boolean; error?: string } {
    // デモ用の簡易アカウント作成
    const storedUsers = JSON.parse(localStorage.getItem('demoUsers') || '{}');
    
    if (storedUsers[username]) {
      return { success: false, error: 'このユーザー名は既に使用されています' };
    }
    
    storedUsers[username] = { email, password };
    localStorage.setItem('demoUsers', JSON.stringify(storedUsers));
    
    return { success: true };
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

      if (response.ok) {
        return { success: true };
      } else {
        const data = await response.json();
        return { success: false, error: data.error || 'パスワードリセットに失敗しました' };
      }
    } catch (error) {
      // APIが利用できない場合は、デモ用に成功を返す
      console.warn('API not available, using demo mode');
      return { success: true };
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

