import axios, { AxiosError } from 'axios'

/// <reference types="vite/client" />

// Type definitions
export type AnalysisResult = {
    rumor: string
    harm: {
        harmfulness_score: number
        [key: string]: any
    }
    harm_score: number
    veracity_score: number
    threat_score: number
}

export type SimulationResult = {
    metrics: {
        cascade_size: number
        time_to_peak: number
        [key: string]: any
    }
    nodes: Array<{
        id: number
        posted_time: number
        stance?: string
        sentiment?: string
        influence: number
    }>
    edges: Array<{
        source: number
        target: number
    }>
}

export type Comment = {
    text: string
    [key: string]: any
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Create axios instance with default config
const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000, // 10 seconds
})

// Error handler
const handleError = (error: unknown) => {
    if (axios.isAxiosError(error)) {
        // Server responded with error status
        const message = error.response?.data?.error || 'Server error'
        throw new Error(message)
    } else if (error instanceof Error) {
        // Request setup error
        throw new Error('Failed to make request: ' + error.message)
    } else {
        // Unknown error
        throw new Error('An unexpected error occurred')
    }
}

// API methods
export const analyzeRumor = async (text: string, comments: Comment[] = []): Promise<AnalysisResult> => {
    try {
        const response = await api.post<AnalysisResult>('/analyze', { text, comments })
        return response.data
    } catch (error) {
        handleError(error)
        // TypeScript needs this even though handleError always throws
        throw new Error('Failed to analyze rumor')
    }
}

export const simulateSpread = async (payload: Record<string, unknown>): Promise<SimulationResult> => {
    try {
        const response = await api.post<SimulationResult>('/simulate', payload)
        return response.data
    } catch (error) {
        handleError(error)
        // TypeScript needs this even though handleError always throws
        throw new Error('Failed to simulate spread')
    }
}

// Export base configuration for use in other parts
export const apiConfig = {
    baseURL: BASE_URL,
}