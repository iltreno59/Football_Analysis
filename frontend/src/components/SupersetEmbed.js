import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Alert } from '@mui/material';
import { embedDashboard } from '@superset-ui/embedded-sdk';

const SupersetEmbed = ({ dashboardId = 1 }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = React.useRef(null);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        
        // Получаем гостевой токен с backend'а
        const tokenResponse = await fetch('http://localhost:8000/api/superset-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!tokenResponse.ok) {
          throw new Error('Не удалось получить токен Superset');
        }
        
        const tokenData = await tokenResponse.json();
        const guestToken = tokenData.token;
        
        // Проверяем доступность Superset
        try {
          await fetch('http://localhost:8080/health', { timeout: 5000 });
        } catch (e) {
          throw new Error('Apache Superset не запущен на http://localhost:8080');
        }
        
        // Встраиваем dashboard с использованием Guest Token
        if (!containerRef.current) {
          throw new Error('Container not found');
        }
        
        await embedDashboard({
          id: dashboardId,
          supersetDomain: 'http://localhost:8080',
          fetchGuestToken: async () => guestToken,
          container: containerRef.current,
          height: '600px',
          width: '100%',
          sandboxAttrs: ['allow-same-origin', 'allow-scripts', 'allow-popups', 'allow-forms'],
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

  return (
    <Box sx={{ position: 'relative' }}>
      {/* Контейнер для встроенного dashboard */}
      <Box
        ref={containerRef}
        id={`superset-dashboard-${dashboardId}`}
        sx={{
          width: '100%',
          height: '600px',
          borderRadius: '8px',
          overflow: 'hidden',
          position: 'relative',
          backgroundColor: loading ? '#f5f5f5' : 'transparent',
          border: '1px solid #ddd',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      >
        {/* Loading состояние */}
        {loading && (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              gap: 2,
              justifyContent: 'center', 
              alignItems: 'center'
            }}
          >
            <CircularProgress />
            <p>Загрузка интерактивной аналитики...</p>
          </Box>
        )}
      </Box>

      {/* Error/Info состояние */}
      {error && (
        <Box sx={{ p: 2, mt: 2 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          
          <Box sx={{ 
            backgroundColor: '#f9f9f9', 
            p: 2, 
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <h4>🚀 Запустите Apache Superset в Docker:</h4>
            <Box
              component="pre"
              sx={{
                backgroundColor: '#2d2d2d',
                color: '#f8f8f2',
                p: 2,
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}
            >
{`# Перейти в корень проекта Football_Analysis
cd d:\\Football_Analysis

# Запустить docker-compose
docker-compose up -d`}
            </Box>
            
            <h4 style={{ marginTop: '20px' }}>📋 Что происходит:</h4>
            <ol style={{ fontSize: '14px', lineHeight: '1.8', marginLeft: '20px' }}>
              <li>PostgreSQL база данных инициализируется</li>
              <li>Superset создает свои таблицы метаданных</li>
              <li>Superset стартует на <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer">http://localhost:8080</a></li>
              <li>Автоматически создается admin аккаунт</li>
              <li>Перезагрузите эту страницу (обычно через 1-2 минуты)</li>
            </ol>
            
            <h4 style={{ marginTop: '20px' }}>🛑 Чтобы остановить:</h4>
            <Box
              component="pre"
              sx={{
                backgroundColor: '#2d2d2d',
                color: '#f8f8f2',
                p: 2,
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}
            >
{`docker-compose down`}
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default SupersetEmbed;
