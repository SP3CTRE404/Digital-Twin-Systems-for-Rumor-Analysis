import { Card } from "@/components/ui/card"

interface ThreatScoreGaugeProps {
  score: number // 0.0 to 1.0
}

export function ThreatScoreGauge({ score }: ThreatScoreGaugeProps) {
  // Clamp score between 0 and 1
  const clampedScore = Math.max(0, Math.min(1, score))

  // Calculate angle for the gauge (180 degrees total, from -90 to +90)
  const angle = clampedScore * 180 - 90

  // Determine color and threat level based on score
  const getColorAndLevel = (score: number) => {
    if (score <= 0.4) {
      return {
        color: "#22c55e", // green-500
        level: "Low Threat",
        bgColor: "bg-green-500/10",
        textColor: "text-green-500",
      }
    } else if (score <= 0.7) {
      return {
        color: "#eab308", // yellow-500
        level: "Medium Threat",
        bgColor: "bg-yellow-500/10",
        textColor: "text-yellow-500",
      }
    } else {
      return {
        color: "#ef4444", // red-500
        level: "High Threat",
        bgColor: "bg-red-500/10",
        textColor: "text-red-500",
      }
    }
  }

  const { color, level, bgColor, textColor } = getColorAndLevel(clampedScore)

  // SVG dimensions
  const size = 280
  const center = size / 2
  const radius = 100
  const strokeWidth = 12

  // Create the arc path for the gauge background
  const createArcPath = (startAngle: number, endAngle: number, innerRadius: number, outerRadius: number) => {
    const start = polarToCartesian(center, center, innerRadius, endAngle)
    const end = polarToCartesian(center, center, innerRadius, startAngle)
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"

    return ["M", start.x, start.y, "A", innerRadius, innerRadius, 0, largeArcFlag, 0, end.x, end.y].join(" ")
  }

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians),
    }
  }

  // Calculate needle position
  const needleEnd = polarToCartesian(center, center, radius - 10, angle)

  return (
    <Card className={`p-8 ${bgColor} border-2`} style={{ borderColor: color + "40" }}>
      <div className="flex flex-col items-center space-y-6">
        <div className="relative">
          <svg width={size} height={size / 2 + 40} className="overflow-visible">
            {/* Background arc */}
            <path
              d={createArcPath(-90, 90, radius, radius)}
              fill="none"
              stroke="hsl(var(--muted))"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Colored progress arc */}
            <path
              d={createArcPath(-90, angle, radius, radius)}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />

            {/* Center dot */}
            <circle cx={center} cy={center} r="8" fill={color} />

            {/* Needle */}
            <line
              x1={center}
              y1={center}
              x2={needleEnd.x}
              y2={needleEnd.y}
              stroke={color}
              strokeWidth="3"
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />

            {/* Scale markers */}
            {[0, 0.25, 0.5, 0.75, 1].map((value, index) => {
              const markerAngle = value * 180 - 90
              const markerStart = polarToCartesian(center, center, radius - 20, markerAngle)
              const markerEnd = polarToCartesian(center, center, radius - 5, markerAngle)

              return (
                <line
                  key={index}
                  x1={markerStart.x}
                  y1={markerStart.y}
                  x2={markerEnd.x}
                  y2={markerEnd.y}
                  stroke="hsl(var(--muted-foreground))"
                  strokeWidth="2"
                />
              )
            })}

            {/* Scale labels */}
            <text
              x={center - 80}
              y={center + 5}
              textAnchor="middle"
              className="fill-muted-foreground text-sm font-medium"
            >
              0.0
            </text>
            <text x={center} y={center - 85} textAnchor="middle" className="fill-muted-foreground text-sm font-medium">
              0.5
            </text>
            <text
              x={center + 80}
              y={center + 5}
              textAnchor="middle"
              className="fill-muted-foreground text-sm font-medium"
            >
              1.0
            </text>
          </svg>
        </div>

        {/* Score display */}
        <div className="text-center space-y-2">
          <div className={`text-4xl font-bold ${textColor}`}>{clampedScore.toFixed(2)}</div>
          <div className={`text-lg font-semibold ${textColor}`}>{level}</div>
          <div className="text-sm text-muted-foreground">Harmfulness Score</div>
        </div>
      </div>
    </Card>
  )
}
