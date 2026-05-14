import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import { embedDashboard } from '@superset-ui/embedded-sdk';

const SupersetEmbed = ({ dashboardId = 1 }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        
        // Инициализируем встраивание Superset dashboard
        // Примечание: в production эти значения должны быть в переменных окружения
        await embedDashboard({
          id: dashboardId,
          supersetDomain: 'http://localhost:8088',
          ownerId: 1,
          fetchGuestToken: async () => {
            // Получаем гостевой токен с backend
            const response = await fetch('http://localhost:8000/api/superset-token', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
              throw new Error('Не удалось получить токен Superset');
            }
            
            const data = await response.json();
            return data.token;
          },
          mounted: (iframe) => {
            // Коллбэк после монтирования
            console.log('Superset dashboard mounted');
          }
        });

        setLoading(false);
      } catch (err) {
        console.error('Error loading Superset dashboard:', err);
        setError(err.message || 'Ошибка при загрузке dashboard');
        setLoading(false);
      }
    };

    loadDashboard();
  }, [dashboardId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">
          {error}
        </Alert>
        <Alert severity="info" sx={{ mt: 2 }}>
          Убедитесь, что Apache Superset запущен на http://localhost:8088
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      id={`superset-dashboard-${dashboardId}`}
      sx={{
        width: '100%',
        height: '600px',
        borderRadius: '8px',
        overflow: 'hidden'
      }}
    />
  );
};

export default SupersetEmbed;
