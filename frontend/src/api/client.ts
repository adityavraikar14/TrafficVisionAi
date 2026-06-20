import axios from "axios";

export const AUTH_STORAGE_KEY = "tv_auth";

// In local dev this stays empty and Vite's dev-server proxy (vite.config.ts)
// forwards /api and /storage to the backend. In production (frontend and
// backend deployed separately, e.g. Vercel + Hugging Face Spaces) there's no
// proxy, so this must point at the real backend URL.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({ baseURL: API_BASE_URL });

// Backend responses return paths like "/storage/evidence/x.jpg" or
// "/api/reports/export.csv" — relative to the backend, not the frontend.
// Anything rendered/linked directly (img src, <a href>) needs this prefix;
// anything sent through `api` already gets it via axios's baseURL.
export const mediaUrl = (path: string | null | undefined): string =>
  path ? `${API_BASE_URL}${path}` : "";

api.interceptors.request.use((config) => {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (raw) {
    const { token } = JSON.parse(raw);
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface Violation {
  id: number;
  violation_id: string;
  vehicle_number: string | null;
  violation_type: string;
  confidence: number;
  status: string;
  city: string | null;
  location: string | null;
  lat: number | null;
  lon: number | null;
  original_image_path: string | null;
  annotated_image_path: string | null;
  source: string;
  created_at: string;
  repeat_count?: number;
}

export interface CityBreakdown {
  city: string;
  total: number;
  helmet: number;
  triple_riding: number;
  illegal_parking: number;
  last_violation_at: string | null;
  lat: number | null;
  lon: number | null;
}

export interface TrendPoint {
  date: string;
  violations: number;
  reviewed: number;
}

export interface AnalyticsSummary {
  total_violations: number;
  helmet_violations: number;
  triple_riding_cases: number;
  pending_reviews: number;
  verified: number;
  escalated: number;
  rejected: number;
  average_confidence: number;
  compliance_rate: number;
  by_type: Record<string, number>;
  city_breakdown: CityBreakdown[];
  trend: TrendPoint[];
  recent: Violation[];
}

export interface PreprocessingReport {
  shadow_correction: boolean;
  low_light_correction: boolean;
  rain_correction: boolean;
  denoise_applied: boolean;
  motion_blur_correction: boolean;
  brightness_score: number;
  sharpness_score: number;
  shadow_spread_score: number;
  rain_streak_score: number;
}

export interface RoadUserDetection {
  category: string;
  class_name: string;
  confidence: number;
  box: number[];
}

export interface RoadUserSummary {
  detections: RoadUserDetection[];
  counts: Record<string, number>;
  total_road_users: number;
}

export interface DetectionResponse {
  vehicle_number: string;
  violations: Violation[];
  annotated_image_url: string;
  original_image_url: string;
  vehicles_detected: number;
  helmet_checks_performed: number;
  is_compliant: boolean;
  preprocessing: PreprocessingReport;
  road_users: RoadUserSummary;
}

export const fetchSummary = () =>
  api.get<AnalyticsSummary>("/api/analytics/summary").then((r) => r.data);

export const fetchEvidence = (search?: string) =>
  api
    .get<Violation[]>("/api/evidence", { params: search ? { search } : {} })
    .then((r) => r.data);

export const updateViolationStatus = (violationId: string, status: string) =>
  api
    .patch<Violation>(`/api/evidence/${violationId}/status`, { status })
    .then((r) => r.data);

export const challanUrl = (violationId: string) => mediaUrl(`/api/evidence/${violationId}/challan.pdf`);

export interface ReviewHistoryEntry {
  id: number;
  violation_id: string;
  decision: string;
  officer_name: string;
  officer_badge_id: string;
  notes: string | null;
  reviewed_at: string;
  violation_type: string;
  vehicle_number: string | null;
  city: string | null;
}

export const submitReview = (
  violationId: string,
  decision: "Verified" | "Rejected",
  officerName: string,
  officerBadgeId: string,
  notes?: string
) =>
  api
    .post<Violation>(`/api/evidence/${violationId}/review`, {
      decision,
      officer_name: officerName,
      officer_badge_id: officerBadgeId,
      notes,
    })
    .then((r) => r.data);

export const fetchReviewHistory = (search?: string) =>
  api
    .get<ReviewHistoryEntry[]>("/api/evidence/history", { params: search ? { search } : {} })
    .then((r) => r.data);

export interface ZoneCalibration {
  enableSignalZone: boolean;
  stopLineY: number;
  signalState: "red" | "yellow" | "green";
  enableParkingZone: boolean;
  zoneTop: number;
  zoneBottom: number;
  zoneLeft: number;
  zoneRight: number;
}

export const analyzeImage = (file: File, zones?: ZoneCalibration) => {
  const formData = new FormData();
  formData.append("file", file);
  if (zones) {
    formData.append("enable_signal_zone", String(zones.enableSignalZone));
    formData.append("stop_line_y", String(zones.stopLineY));
    formData.append("signal_state", zones.signalState);
    formData.append("enable_parking_zone", String(zones.enableParkingZone));
    formData.append("zone_top", String(zones.zoneTop));
    formData.append("zone_bottom", String(zones.zoneBottom));
    formData.append("zone_left", String(zones.zoneLeft));
    formData.append("zone_right", String(zones.zoneRight));
  }
  return api
    .post<DetectionResponse>("/api/detect/image", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const exportReportUrl = mediaUrl("/api/reports/export.csv");

export interface VideoDetectionResponse {
  vehicles_tracked: number;
  frames_processed: number;
  video_duration_sec: number;
  violations: Violation[];
  is_compliant: boolean;
}

export const analyzeVideo = (file: File, correctDirectionAngle: number) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("correct_direction_angle", String(correctDirectionAngle));
  return api
    .post<VideoDetectionResponse>("/api/detect/video", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};
