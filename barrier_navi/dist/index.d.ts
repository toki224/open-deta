/**
 * バリアナビ（身体障害向け）フロントエンド
 */
interface ApiResponse<T> {
    success: boolean;
    data?: T;
    count?: number;
    total_count?: number;
    error?: string;
}
interface BodyScoreSummary {
    met_items: number;
    total_items: number;
    percentage: number;
    label: string;
    weighted_score?: number;
    max_weighted_score?: number;
}
interface BodyStationSummary {
    station_id: number;
    station_name: string;
    prefecture: string;
    city: string;
    operator: string;
    line_name: string;
    score: BodyScoreSummary;
}
interface BodyMetricDetail {
    key: string;
    label: string;
    value: number | string | null;
    raw_value: number | string | null;
    required: number;
    ratio: number;
    met: boolean;
    type: string;
    weight: number;
}
interface BodyStationDetail extends BodyStationSummary {
    metrics: BodyMetricDetail[];
}
interface BodyMetricDefinition {
    key: string;
    label: string;
    required: number;
    type: 'flag' | 'number';
}
declare const BODY_METRICS: BodyMetricDefinition[];
declare class StationApp {
    private apiBaseUrl;
    private currentPage;
    private pageSize;
    private selectedPrefecture;
    private keyword;
    private lastResultCount;
    private totalCount;
    private selectedFilters;
    private sortOrder;
    constructor();
    private init;
    private renderFilterControls;
    private setupEventListeners;
    private applySearch;
    private resetFilters;
    private collectFilters;
    private loadPrefectures;
    private fetchApi;
    private loadStations;
    private updateActiveFilters;
    private renderStationCards;
    private updatePagination;
    private navigateToDetail;
    private escapeHtml;
}
//# sourceMappingURL=index.d.ts.map