import React from 'react';

// A flexible and reusable Card component system.
// This allows for consistent styling across the application.

const Card = ({ children, className = '' }) => (
  <div className={`bg-white border border-gray-200 rounded-xl shadow-sm ${className}`}>
    {children}
  </div>
);

const CardHeader = ({ children, className = '' }) => (
  <div className={`p-4 sm:p-6 border-b border-gray-200 ${className}`}>
    {children}
  </div>
);

const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-lg font-semibold text-gray-800 ${className}`}>
    {children}
  </h3>
);

const CardContent = ({ children, className = '' }) => (
  <div className={`p-4 sm:p-6 ${className}`}>
    {children}
  </div>
);

export { Card, CardHeader, CardTitle, CardContent };
