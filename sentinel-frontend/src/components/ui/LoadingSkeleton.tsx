import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Threat Score Gauge Skeleton */}
      <Card className="p-6">
        <div className="flex flex-col items-center space-y-4">
          <Skeleton className="h-32 w-64 rounded-full" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-32" />
        </div>
      </Card>

      {/* Fact Check Card Skeleton */}
      <Card className="p-6">
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-16 w-full" />
        </div>
      </Card>

      {/* Metrics Grid Skeleton */}
      <div className="grid grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-6 w-16" />
            </div>
          </Card>
        ))}
      </div>

      {/* Simulated Conversation Skeleton */}
      <Card className="p-6">
        <Skeleton className="h-6 w-48 mb-4" />
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="border rounded-lg p-3 space-y-2">
              <div className="flex items-center space-x-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
              <Skeleton className="h-12 w-full" />
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
