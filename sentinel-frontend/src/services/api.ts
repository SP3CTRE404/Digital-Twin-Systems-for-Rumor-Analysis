import axios from "axios"
import type { AnalysisRequest, AnalysisResponse } from "../types/api"

const API_BASE_URL = "http://127.0.0.1:5000"

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

export const analyzeRumor = async (rumor: string): Promise<AnalysisResponse> => {
  const request: AnalysisRequest = { rumor }
  const response = await apiClient.post<AnalysisResponse>("/analyze", request)
  return response.data
}
