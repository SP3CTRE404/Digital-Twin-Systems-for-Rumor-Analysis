import { Card } from "@/components/ui/card"
import type { FactCheck } from "../../types/api"

interface FactCheckCardProps {
  factCheckData: FactCheck
}

export function FactCheckCard({ factCheckData }: FactCheckCardProps) {
  const getStatusConfig = (status: FactCheck["status"]) => {
    switch (status) {
      case "Verified":
        return {
          icon: "✓",
          bgColor: "bg-green-500/10",
          borderColor: "border-green-500/30",
          textColor: "text-green-500",
          iconBg: "bg-green-500/20",
        }
      case "False":
        return {
          icon: "✗",
          bgColor: "bg-red-500/10",
          borderColor: "border-red-500/30",
          textColor: "text-red-500",
          iconBg: "bg-red-500/20",
        }
      case "Misleading":
        return {
          icon: "⚠",
          bgColor: "bg-orange-500/10",
          borderColor: "border-orange-500/30",
          textColor: "text-orange-500",
          iconBg: "bg-orange-500/20",
        }
      case "Unverified":
        return {
          icon: "?",
          bgColor: "bg-yellow-500/10",
          borderColor: "border-yellow-500/30",
          textColor: "text-yellow-500",
          iconBg: "bg-yellow-500/20",
        }
      default:
        return {
          icon: "?",
          bgColor: "bg-gray-500/10",
          borderColor: "border-gray-500/30",
          textColor: "text-gray-500",
          iconBg: "bg-gray-500/20",
        }
    }
  }

  const config = getStatusConfig(factCheckData.status)

  return (
    <Card className={`p-6 ${config.bgColor} ${config.borderColor} border-2`}>
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <div className={`h-10 w-10 rounded-full ${config.iconBg} flex items-center justify-center`}>
            <span className={`text-lg font-bold ${config.textColor}`}>{config.icon}</span>
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${config.textColor}`}>Fact Check: {factCheckData.status}</h3>
            <p className="text-sm text-muted-foreground">Verification Status</p>
          </div>
        </div>

        <div className="pl-13">
          <p className="text-foreground leading-relaxed">{factCheckData.details}</p>
        </div>
      </div>
    </Card>
  )
}
