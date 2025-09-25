import type { Comment } from "../../types/api"

interface CommentCardProps {
  comment: Comment
}

export function CommentCard({ comment }: CommentCardProps) {
  const getStanceConfig = (stance: Comment["stance"]) => {
    switch (stance) {
      case "support":
        return {
          icon: "👍",
          bgColor: "bg-green-500/10",
          borderColor: "border-l-green-500",
          textColor: "text-green-500",
        }
      case "deny":
        return {
          icon: "👎",
          bgColor: "bg-red-500/10",
          borderColor: "border-l-red-500",
          textColor: "text-red-500",
        }
      case "query":
        return {
          icon: "❓",
          bgColor: "bg-yellow-500/10",
          borderColor: "border-l-yellow-500",
          textColor: "text-yellow-500",
        }
      default:
        return {
          icon: "💬",
          bgColor: "bg-gray-500/10",
          borderColor: "border-l-gray-500",
          textColor: "text-gray-500",
        }
    }
  }

  const getUserTypeColor = (userType: Comment["user_type"]) => {
    switch (userType) {
      case "supporter":
        return "text-green-600"
      case "denier":
        return "text-red-600"
      case "skeptic":
        return "text-yellow-600"
      default:
        return "text-muted-foreground"
    }
  }

  const config = getStanceConfig(comment.stance)

  return (
    <div
      className={`border rounded-lg p-4 ${config.bgColor} border-l-4 ${config.borderColor} hover:shadow-sm transition-shadow`}
    >
      <div className="space-y-3">
        {/* User info header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm">{config.icon}</span>
            <span className="font-medium text-foreground">{comment.username}</span>
            <span className={`text-xs px-2 py-1 rounded-full bg-muted ${getUserTypeColor(comment.user_type)}`}>
              {comment.user_type}
            </span>
          </div>
          <div className={`text-xs font-medium ${config.textColor} capitalize`}>{comment.stance}</div>
        </div>

        {/* Comment text */}
        <div className="text-sm text-foreground leading-relaxed">{comment.comment_text}</div>
      </div>
    </div>
  )
}
