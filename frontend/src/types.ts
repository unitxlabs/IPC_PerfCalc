export interface IPCModel {
  id: number;
  name: string;
  cpu_model?: string | null;
  ram?: string | null;
  gpu_info?: string | null;
  ssd?: string | null;
  hdd?: string | null;
}

export interface TestRecord {
  id: number;
  ipc_model: IPCModel;
  software_version: string;
  resolution_mp: number;
  camera_count: number;
  model_count: number;
  segments_count: number;
  image_count?: number | null;
  save_image?: boolean | null;
  measured_perf_mps: number;
  ex_perf_mps?: number | null;
  created_at?: string | null;
}

export interface OptionsResponse {
  ipc_models: IPCModel[];
  resolutions: number[];
  camera_counts: number[];
  model_counts: number[];
  software_versions: string[];
}

export interface RecordSearchRequest {
  ipc_model_ids?: number[];
  resolution_mp?: number | null;
  camera_count?: number | null;
  model_count?: number | null;
  software_versions?: string[];
}

export interface ImportResult {
  inserted: number;
  skipped: number;
  errors?: string[] | null;
}
