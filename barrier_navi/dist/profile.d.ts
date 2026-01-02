/**
 * バリアナビ プロフィール画面
 */
interface ProfileData {
    username: string;
    email: string;
    disability_type?: string[];
    favorite_stations?: number[];
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
declare class ProfilePage {
    private apiBaseUrl;
    private userId;
    private favoriteStations;
    private stationSearchTimeout;
    constructor();
    private init;
    private checkAuthStatus;
    private setupEventListeners;
    private debounceSearch;
    private searchStations;
    private showStationSearchResults;
    private hideStationSearchResults;
    private addFavoriteStation;
    private removeFavoriteStation;
    private removeFavoriteStationByName;
    private renderFavoriteStations;
    private loadProfile;
    private loadUserInfo;
    private populateForm;
    private loadFavoriteStationNamesFromIds;
    private loadFavoriteStationNamesFromNames;
    private handleSubmit;
    private saveProfile;
    private showError;
    private isValidEmail;
    private escapeHtml;
}
//# sourceMappingURL=profile.d.ts.map