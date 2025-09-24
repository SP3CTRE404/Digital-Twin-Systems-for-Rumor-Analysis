import React, { useState } from 'react';
import { analyzeRumor } from '../api/api.jsx'; // Assuming your API call function is here

// Import UI Components
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card.jsx';
import { Skeleton } from '../components/ui/Skeleton.jsx';
import AnalysisResults from '../components/AnalysisResults.jsx';

const Dashboard = () => {
  const [rumorText, setRumorText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalysis = async () => {
    if (!rumorText.trim()) {
      setError('Please enter a rumor to analyze.');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const result = await analyzeRumor({ rumor_text: rumorText });
      setAnalysis(result);
    } catch (err) {
      setError('Failed to analyze the rumor. The server might be down or an error occurred. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Digital Twin: Rumor Threat Analysis</h1>
          <p className="text-lg text-gray-600 mt-2">
            Enter a rumor or suspicious text below to simulate its potential spread and assess its harmfulness score.
          </p>
        </header>

        <main>
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Rumor Input</CardTitle>
            </CardHeader>
            <CardContent>
              <textarea
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
                rows="4"
                placeholder="e.g., 'Scientists have discovered a new species of glowing mushrooms...'"
                value={rumorText}
                onChange={(e) => setRumorText(e.target.value)}
                disabled={isLoading}
              />
              <button
                onClick={handleAnalysis}
                className="mt-4 w-full sm:w-auto px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
                disabled={isLoading}
              >
                {isLoading ? 'Analyzing...' : 'Analyze Threat'}
              </button>
            </CardContent>
          </Card>
          
          {error && (
            <Card className="border-red-500 bg-red-50">
              <CardHeader>
                <CardTitle className="text-red-700">An Error Occurred</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-red-600">{error}</p>
              </CardContent>
            </Card>
          )}

          {isLoading && <LoadingSkeleton />}
          {analysis && !isLoading && <AnalysisResults data={analysis} />}
        </main>
      </div>
    </div>
  );
};

// A skeleton component to show while data is loading
const LoadingSkeleton = () => (
  <div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card>
        <CardHeader><Skeleton className="h-6 w-3/4" /></CardHeader>
        <CardContent><Skeleton className="h-24 w-full" /></CardContent>
      </Card>
      <Card>
        <CardHeader><Skeleton className="h-6 w-3/4" /></CardHeader>
        <CardContent><Skeleton className="h-24 w-full" /></CardContent>
      </Card>
      <Card>
        <CardHeader><Skeleton className="h-6 w-3/4" /></CardHeader>
        <CardContent><Skeleton className="h-24 w-full" /></CardContent>
      </Card>
    </div>
  </div>
);


export default Dashboard;

