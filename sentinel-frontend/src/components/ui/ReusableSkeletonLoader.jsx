import React from 'react';

// A simple skeleton component to indicate a loading state.
// Provides a better UX than a simple "Loading..." text.
const Skeleton = ({ className = '' }) => (
  <div className={`bg-gray-200 rounded-md animate-pulse ${className}`} />
);

export { Skeleton };
    