import React from 'react'
import { Outlet } from 'react-router-dom'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      <header className="p-4 bg-blue-600 text-white text-xl font-bold">
        SENTINEL-X Dashboard
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}


