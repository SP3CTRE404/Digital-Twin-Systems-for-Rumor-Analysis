import React from 'react'

export default function AnalysisResults({ analysis }) {
    if (!analysis) return null

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h2 className="text-xl font-bold mb-4">Rumor Analysis</h2>
            <div className="space-y-4">
                <div>
                    <h3 className="font-semibold">Rumor Text:</h3>
                    <p className="text-gray-700">{analysis.rumor}</p>
                </div>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <h3 className="font-semibold">Harm Score:</h3>
                        <p className={`text-lg font-bold ${analysis.harm_score > 0.6 ? 'text-red-600' :
                                analysis.harm_score > 0.3 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                            {(analysis.harm_score * 100).toFixed(1)}%
                        </p>
                    </div>
                    <div>
                        <h3 className="font-semibold">Veracity Score:</h3>
                        <p className={`text-lg font-bold ${analysis.veracity_score > 0.6 ? 'text-green-600' :
                                analysis.veracity_score > 0.3 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                            {(analysis.veracity_score * 100).toFixed(1)}%
                        </p>
                    </div>
                    <div>
                        <h3 className="font-semibold">Threat Score:</h3>
                        <p className={`text-lg font-bold ${analysis.threat_score > 0.6 ? 'text-red-600' :
                                analysis.threat_score > 0.3 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                            {(analysis.threat_score * 100).toFixed(1)}%
                        </p>
                    </div>
                </div>
                {analysis.harm?.components && (
                    <div className="mt-4">
                        <h3 className="font-semibold mb-2">Analysis Components:</h3>
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(analysis.harm.components).map(([key, value]) => (
                                <div key={key} className="bg-gray-50 p-3 rounded">
                                    <h4 className="text-sm font-medium text-gray-600">
                                        {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                                    </h4>
                                    <p className="text-sm">{typeof value === 'object' ? JSON.stringify(value) : value}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}