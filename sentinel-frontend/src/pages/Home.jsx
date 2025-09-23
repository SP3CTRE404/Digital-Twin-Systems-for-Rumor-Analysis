import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeRumor, simulateSpread } from '../api/client'

export default function Home() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!text.trim()) {
      setError('Please enter a rumor to analyze')
      return
    }

    setLoading(true)
    setError('')

    try {
      // First analyze the rumor
      const analysisResult = await analyzeRumor(text)

      // Then run the simulation
      const simulationResult = await simulateSpread({
        text,
        steps: 400,
        harm_score: analysisResult.harm_score,
        veracity_score: analysisResult.veracity_score
      })

      // Navigate to dashboard with both results
      navigate('/dashboard', {
        state: {
          analysis: analysisResult,
          simulation: simulationResult
        }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze rumor')
      console.error('Request failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center mt-20">
      <h1 className="text-2xl font-bold mb-5">Rumor Analysis and Simulation</h1>

      {error && (
        <div className="text-red-500 mb-4">{error}</div>
      )}

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter rumor here..."
        className="border p-3 w-96 h-28 rounded"
        disabled={loading}
      />

      <button
        onClick={handleSubmit}
        className={`px-5 py-2 mt-4 rounded text-white ${loading
            ? 'bg-blue-300 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600'
          }`}
        disabled={loading}
      >
        {loading ? 'Analyzing...' : 'Analyze & Simulate'}
      </button>
    </div>
  )
}


