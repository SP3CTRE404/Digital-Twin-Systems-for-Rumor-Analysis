import { Card } from "@/components/ui/card"
import type { DetailedMetrics } from "../../types/api"

interface MetricsGridProps {
  metrics: DetailedMetrics
}

export function MetricsGrid({ metrics }: MetricsGridProps) {
  if (!metrics) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">Detailed Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((index) => (
            <Card key={index} className="p-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 bg-muted rounded animate-pulse" />
                    <div className="w-24 h-4 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="w-12 h-6 bg-muted rounded animate-pulse" />
                </div>
                <div className="w-full h-3 bg-muted rounded animate-pulse" />
                <div className="w-full h-2 bg-muted rounded animate-pulse" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1) + "%"
  }

  const getScoreColor = (score: number) => {
    if (score <= 0.4) return "text-green-500"
    if (score <= 0.7) return "text-yellow-500"
    return "text-red-500"
  }

  const metricsData = [
    {
      label: "Sentiment Score",
      value: metrics.sentimentScore ?? 0,
      description: "Overall emotional tone analysis",
      icon: "💭",
    },
    {
      label: "Stance Score",
      value: metrics.stanceScore ?? 0,
      description: "Position strength measurement",
      icon: "📊",
    },
    {
      label: "Organization Score",
      value: metrics.organizationScore ?? 0,
      description: "Structural coherence rating",
      icon: "🏗️",
    },
    {
      label: "Raw Harmfulness",
      value: metrics.rawHarmfulnessScore ?? 0,
      description: "Unprocessed threat assessment",
      icon: "⚡",
    },
  ]

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-foreground">Detailed Metrics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metricsData.map((metric, index) => (
          <Card key={index} className="p-4 hover:shadow-md transition-shadow">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{metric.icon}</span>
                  <h4 className="font-medium text-foreground">{metric.label}</h4>
                </div>
                <div className={`text-xl font-bold ${getScoreColor(metric.value)}`}>{formatScore(metric.value)}</div>
              </div>

              <p className="text-sm text-muted-foreground">{metric.description}</p>

              {/* Progress bar */}
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    metric.value <= 0.4 ? "bg-green-500" : metric.value <= 0.7 ? "bg-yellow-500" : "bg-red-500"
                  }`}
                  style={{ width: `${metric.value * 100}%` }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
