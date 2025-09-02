import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const usePhraseMappings = (reportType: 'transplant' | 'native') => {
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMappings = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get(`${API_URL}/api/phrases/${reportType}`);
        setMappings(response.data);
      } catch (err) {
        console.error('Error fetching phrase mappings:', err);
        setError('Failed to load phrase mappings');
        setMappings({});
      } finally {
        setLoading(false);
      }
    };

    fetchMappings();
  }, [reportType]);

  return { mappings, loading, error };
};