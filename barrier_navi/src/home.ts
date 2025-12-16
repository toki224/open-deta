/**
 * バリアナビ ホーム画面
 */

class HomePage {
  constructor() {
    this.init();
  }

  private init(): void {
    const profileBtn = document.getElementById('profile-btn');
    profileBtn?.addEventListener('click', () => {
      // プロフィール画面への遷移（未実装の場合はアラート）
      alert('プロフィール画面は準備中です');
      // 実装時は以下のように変更
      // window.location.href = 'profile.html';
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new HomePage();
});

