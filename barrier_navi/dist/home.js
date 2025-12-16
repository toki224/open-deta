/**
 * バリアナビ ホーム画面
 */
class HomePage {
    constructor() {
        this.init();
    }
    init() {
        const profileBtn = document.getElementById('profile-btn');
        profileBtn === null || profileBtn === void 0 ? void 0 : profileBtn.addEventListener('click', () => {
            alert('プロフィール画面は準備中です');
        });
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new HomePage();
});

