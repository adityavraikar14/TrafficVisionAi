import axios from "axios";

export const api = axios.create({ baseURL: "" });

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
}

export interface CityBreakdown {
  city: string;
  total: number;
  helmet: number;
  triple_riding: number;
  illegal_parking: number;
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
  average_confidence: number;
  compliance_rate: number;
  by_type: Record<string, number>;
  city_breakdown: CityBreakdown[];
  trend: TrendPoint[];
  recent: Violation[];
}

export interface PreprocessingReport {
  low_light_correction: boolean;
  denoise_applied: boolean;
  motion_blur_correction: boolean;
  brightness_score: number;
  sharpness_score: number;
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

export const exportReportUrl = "/api/reports/export.csv";
