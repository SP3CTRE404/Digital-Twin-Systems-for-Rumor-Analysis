import { Card } from "@/components/ui/card"
import type { Comment } from "../../types/api"
import { CommentCard } from "./CommentCard"

interface SimulatedConversationProps {
  comments: Comment[]
}

export function SimulatedConversation({ comments }: SimulatedConversationProps) {
  const getStanceStats = (comments: Comment[]) => {
    const stats = comments.reduce(
      (acc, comment) => {
        acc[comment.stance] = (acc[comment.stance] || 0) + 1
        return acc
      },
      {} as Record<string, number>,
    )

    return stats
  }

  const stats = getStanceStats(comments)

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header with stats */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Simulated Conversation Thread</h3>
            <div className="text-sm text-muted-foreground">{comments.length} comments</div>
          </div>

          {/* Stance distribution */}
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-1">
              <span>👍</span>
              <span className="text-green-500 font-medium">{stats.support || 0} Support</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>👎</span>
              <span className="text-red-500 font-medium">{stats.deny || 0} Deny</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>❓</span>
              <span className="text-yellow-500 font-medium">{stats.query || 0} Question</span>
            </div>
          </div>
        </div>

        {/* Comments container */}
        <div className="max-h-96 overflow-y-auto space-y-3 pr-2">
          {comments.length > 0 ? (
            comments.map((comment, index) => <CommentCard key={index} comment={comment} />)
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl">💬</span>
              </div>
              <p>No simulated comments available</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
