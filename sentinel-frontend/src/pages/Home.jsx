import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Home() {
  const [text, setText] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5000/simulate_digital_twin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, steps: 400 })
      })
      if (!res.ok) {
        const txt = await res.text()
        console.error('Backend error', res.status, txt)
        return
      }
      const data = await res.json()
      navigate('/dashboard', { state: { result: data } })
    } catch (e) {
      console.error('Request failed', e)
    }
  }

  return (
    <div className="flex flex-col items-center mt-20">
      <h1 className="text-2xl font-bold mb-5">Rumor Simulation</h1>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter rumor here..."
        className="border p-3 w-96 h-28"
      />
      <button
        onClick={handleSubmit}
        className="bg-blue-500 text-white px-5 py-2 mt-4 rounded"
      >
        Simulate
      </button>
    </div>
  )
}


