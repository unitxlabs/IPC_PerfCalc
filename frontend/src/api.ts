import axios from "axios";
import type {
  OptionsResponse,
  RecordSearchRequest,
  TestRecord,
  ImportResult
} from "./types";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
  timeout: 15000
});

export async function fetchOptions(): Promise<OptionsResponse> {
  const { data } = await client.get<OptionsResponse>("/api/v1/options");
  return data;
}

export async function searchRecords(
  payload: RecordSearchRequest
): Promise<TestRecord[]> {
  const { data } = await client.post<TestRecord[]>(
    "/api/v1/records/search",
    payload
  );
  return data;
}

export async function importRecords(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<ImportResult>(
    "/api/v1/records/import",
    form,
    {
      headers: { "Content-Type": "multipart/form-data" }
    }
  );
  return data;
}
