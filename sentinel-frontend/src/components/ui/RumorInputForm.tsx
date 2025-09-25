"use client"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card } from "@/components/ui/card"

interface RumorInputFormProps {
  rumorText: string
  setRumorText: (text: string) => void
  onAnalyze: () => void
  isLoading: boolean
}

export function RumorInputForm({ rumorText, setRumorText, onAnalyze, isLoading }: RumorInputFormProps) {
  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <label htmlFor="rumor-input" className="block text-sm font-medium mb-2">
            Enter rumor text to analyze
          </label>
          <Textarea
            id="rumor-input"
            placeholder="Paste the rumor or claim you want to analyze for potential threats..."
            value={rumorText}
            onChange={(e) => setRumorText(e.target.value)}
            className="min-h-32 resize-none"
            disabled={isLoading}
          />
        </div>
        <Button onClick={onAnalyze} disabled={isLoading || !rumorText.trim()} className="w-full">
          {isLoading ? "Analyzing..." : "Analyze Rumor"}
        </Button>
      </div>
    </Card>
  )
}
