export interface FactCheck {
  status: "Verified" | "False" | "Misleading" | "Unverified"
  details: string
}

export interface DetailedMetrics {
  sentimentScore: number
  stanceScore: number
  organizationScore: number
  rawHarmfulnessScore: number
}

export interface Comment {
  username: string
  user_type: "supporter" | "denier" | "skeptic"
  comment_text: string
  stance: "support" | "deny" | "query"
}

export interface AnalysisResponse {
  harmfulnessScore: number // This is the main score from 0.0 to 1.0
  factCheck: FactCheck
  detailedMetrics: DetailedMetrics
  simulatedComments: Comment[]
}

export interface AnalysisRequest {
  rumor: string
}
