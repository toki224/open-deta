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
    ratio: number;
    met: boolean;
    type: string;
}
interface BodyStationDetail extends BodyStationSummary {
    metrics: BodyMetricDetail[];
}
interface BodyMetricDefinition {
    key: string;
    label: string;
    required: number;
    type: 'flag' | 'number' | 'ratio';
}
declare const BODY_METRICS: BodyMetricDefinition[];
declare const HEARING_METRICS: BodyMetricDefinition[];
declare const VISION_METRICS: BodyMetricDefinition[];
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
    private currentMode;
    private currentMetrics;
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
    private fetchLines;
}
//# sourceMappingURL=index.d.ts.map