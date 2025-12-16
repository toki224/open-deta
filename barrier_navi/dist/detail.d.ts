interface DetailApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
}
interface DetailScore {
    met_items: number;
    total_items: number;
    percentage: number;
    label: string;
}
interface DetailMetric {
    key: string;
    label: string;
    value: number | string | null;
    required: number;
    ratio: number;
    met: boolean;
}
interface DetailStation {
    station_id: number;
    station_name: string;
    prefecture: string;
    city: string;
    operator: string;
    line_name: string;
    score: DetailScore;
    metrics: DetailMetric[];
}
declare class DetailPage {
    private apiBaseUrl;
    private titleEl;
    private scoreEl;
    private metaEl;
    private tableBodyEl;
    constructor();
    private load;
    private fetchApi;
    private renderDetail;
    private renderError;
    private escape;
}
//# sourceMappingURL=detail.d.ts.map