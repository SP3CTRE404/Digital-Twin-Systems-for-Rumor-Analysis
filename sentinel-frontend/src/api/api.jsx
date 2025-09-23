const BASE_URL = import.meta?.env?.VITE_API_URL || 'http://localhost:5000'

export async function analyzeText(text) {
  const res = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  })
  if (!res.ok) throw new Error(`Analyze failed: ${res.status}`)
  return res.json()
}

export async function simulate(payload) {
  const res = await fetch(`${BASE_URL}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {})
  })
  if (!res.ok) throw new Error(`Simulate failed: ${res.status}`)
  return res.json()
}


