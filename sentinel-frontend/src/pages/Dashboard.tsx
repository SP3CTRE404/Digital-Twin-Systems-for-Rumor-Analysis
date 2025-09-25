"use client"

import { useState } from "react"
import type { AnalysisResponse } from "../types/api"
import { analyzeRumor } from "../services/api"
import { RumorInputForm } from "../components/ui/RumorInputForm"
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton"
import { ThreatScoreGauge } from "../components/results/ThreatScoreGauge"
import { FactCheckCard } from "../components/results/FactCheckCard"
import { MetricsGrid } from "../components/results/MetricsGrid"
import { SimulatedConversation } from "../components/results/SimulatedConversation"

export function Dashboard() {
  const [rumorText, setRumorText] = useState<string>("")
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyzeRumor = async () => {
    if (!rumorText.trim()) return

    setIsLoading(true)
    setError(null)
    setAnalysisResult(null)

    try {
      const result = await analyzeRumor(rumorText)
      setAnalysisResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred while analyzing the rumor")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">S</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Sentinel</h1>
              <p className="text-sm text-muted-foreground">Digital Twin Rumor Analysis System</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Input Form */}
          <RumorInputForm
            rumorText={rumorText}
            setRumorText={setRumorText}
            onAnalyze={handleAnalyzeRumor}
            isLoading={isLoading}
          />

          {/* Results Section */}
          <div className="space-y-6">
            {!analysisResult && !isLoading && !error && (
              <div className="text-center py-12">
                <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🔍</span>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">Ready to Analyze</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Enter a rumor or claim above to get a comprehensive threat analysis including fact-checking, sentiment
                  analysis, and simulated community response.
                </p>
              </div>
            )}

            {isLoading && <LoadingSkeleton />}

            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 text-center">
                <div className="h-12 w-12 bg-destructive/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-destructive text-xl">⚠</span>
                </div>
                <h3 className="text-lg font-semibold text-destructive mb-2">Analysis Failed</h3>
                <p className="text-destructive/80">{error}</p>
              </div>
            )}

            {analysisResult && (
              <div className="space-y-6">
                {/* Threat Score Gauge */}
                <ThreatScoreGauge score={analysisResult.harmfulnessScore} />

                {/* Fact Check Card */}
                <FactCheckCard factCheckData={analysisResult.factCheck} />

                {/* Metrics Grid */}
                <MetricsGrid metrics={analysisResult.detailedMetrics} />

                {/* Simulated Conversation */}
                <SimulatedConversation comments={analysisResult.simulatedComments} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
