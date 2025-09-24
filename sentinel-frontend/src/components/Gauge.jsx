import React from 'react';

const Gauge = ({ value = 0 }) => {
  const score = Math.max(0, Math.min(100, Math.round(value * 100)));
  const circumference = 2 * Math.PI * 45; // Circle radius is 45
  const offset = circumference - (score / 100) * circumference;

  const getColor = (val) => {
    if (val > 75) return '#ef4444'; // Red
    if (val > 40) return '#f59e0b'; // Amber
    return '#22c55e'; // Green
  };

  const color = getColor(score);

  return (
    <div className="relative flex items-center justify-center w-48 h-48">
      <svg className="w-full h-full" viewBox="0 0 100 100">
        {/* Background Circle */}
        <circle
          className="text-gray-200"
          strokeWidth="10"
          stroke="currentColor"
          fill="transparent"
          r="45"
          cx="50"
          cy="50"
        />
        {/* Progress Circle */}
        <circle
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          stroke={color}
          fill="transparent"
          r="45"
          cx="50"
          cy="50"
          style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-4xl font-bold" style={{ color }}>
          {score}
        </span>
        <span className="text-sm text-gray-500">Risk Score</span>
      </div>
    </div>
  );
};

export default Gauge;
