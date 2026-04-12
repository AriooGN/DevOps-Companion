"use client"
import OverViewPage from './_components/overview';

import { useState, useEffect } from 'react';
// export const metadata = {
//   title: 'Dashboard : Overview'
// };


export default function Page() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000); 

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return ( <div className="loading-overlay">
      <div className="loading-content">
        <img src="/Loader.gif" alt="Loading..." />
      </div>
    </div>)
  }

  return <OverViewPage />;
}

