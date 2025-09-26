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
  const response = await apiClient.post<any>("/analyze", request)

  const pythonResponse = response.data

  let factCheckDetails = "Fact check analysis completed"

  if (pythonResponse.veracity_details) {
    if (typeof pythonResponse.veracity_details === "string") {
      factCheckDetails = pythonResponse.veracity_details
    } else if (
      pythonResponse.veracity_details.analysis_summary &&
      typeof pythonResponse.veracity_details.analysis_summary === "string"
    ) {
      factCheckDetails = pythonResponse.veracity_details.analysis_summary
    } else if (
      pythonResponse.veracity_details.avg_confidence !== undefined &&
      pythonResponse.veracity_details.total_fact_checks !== undefined
    ) {
      // Handle the case where veracity_details contains avg_confidence and total_fact_checks
      factCheckDetails = `Analysis completed with ${pythonResponse.veracity_details.total_fact_checks} fact checks and ${(pythonResponse.veracity_details.avg_confidence * 100).toFixed(1)}% average confidence`
    }
  }

  return {
    harmfulnessScore: pythonResponse.harm_score || pythonResponse.harmfulness_score || 0,
    factCheck: {
      status: getFactCheckStatus(pythonResponse.veracity_score),
      details: factCheckDetails,
    },
    detailedMetrics: {
      sentimentScore: pythonResponse.harm?.components?.sentiment_score || 0,
      stanceScore: pythonResponse.harm?.components?.stance_score || 0,
      organizationScore: pythonResponse.harm?.components?.organization_score || 0,
      rawHarmfulnessScore: pythonResponse.harm_score || 0,
    },
    simulatedComments: transformComments(pythonResponse.comments_sample || []),
  }
}

function getFactCheckStatus(veracityScore: number): "Verified" | "False" | "Misleading" | "Unverified" {
  if (veracityScore >= 0.8) return "Verified"
  if (veracityScore <= 0.3) return "False"
  if (veracityScore >= 0.4 && veracityScore <= 0.7) return "Misleading"
  return "Unverified"
}

function transformComments(pythonComments: any[]): any[] {
  return pythonComments.map((comment) => ({
    username: comment["user.handle"] || comment.username || "anonymous",
    user_type: mapUserType(comment.user_type || comment.stance),
    comment_text: comment.text || comment.comment_text || "",
    stance: mapStance(comment.stance || "comment"),
  }))
}

function mapUserType(type: string): "supporter" | "denier" | "skeptic" {
  if (!type) return "skeptic"
  const lowerType = type.toLowerCase()
  if (lowerType.includes("support")) return "supporter"
  if (lowerType.includes("deny") || lowerType.includes("false")) return "denier"
  return "skeptic"
}

function mapStance(stance: string): "support" | "deny" | "query" {
  if (!stance) return "query"
  const lowerStance = stance.toLowerCase()
  if (lowerStance.includes("support")) return "support"
  if (lowerStance.includes("deny")) return "deny"
  return "query"
}
