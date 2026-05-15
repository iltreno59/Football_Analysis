import React, { useEffect, useState, useRef } from 'react';
import { Box, CircularProgress, Alert, Typography } from '@mui/material';
import { embedDashboard } from '@superset-ui/embedded-sdk';

const SupersetEmbed = ({ dashboardId = "1" }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  // Реф для отслеживания, что встраивание уже запущено
  const isEmbedded = useRef(false);

  useEffect(() => {
    const loadDashboard = async () => {
      // Предотвращаем повторную инициализацию в StrictMode или при перерисовках
      if (isEmbedded.current) return;

      try {
        setLoading(true);
        setError(null);

        // 1. Получаем гостевой токен с backend'а
        const tokenResponse = await fetch('http://localhost:8000/api/superset-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!tokenResponse.ok) {
          throw new Error('Не удалось получить токен Superset');
        }
        
        const tokenData = await tokenResponse.json();
        const guestToken = tokenData.token;

        // 2. Проверяем доступность Superset перед встраиванием
        try {
          const healthCheck = await fetch('http://localhost:8080/health', { mode: 'no-cors' });
        } catch (e) {
          throw new Error('Apache Superset не доступен на http://localhost:8080');
        }

        // 3. Встраиваем dashboard
        if (containerRef.current) {
          isEmbedded.current = true;
          await embedDashboard({
            id: dashboardId, // UUID вашего дашборда
            supersetDomain: 'http://localhost:8080',
            mountPoint: containerRef.current, // Используем mountPoint вместо container
            fetchGuestToken: async () => guestToken,
            dashboardUiConfig: { 
              hideTitle: true, 
              hideTab: true,
            },
          });
          setLoading(false);
        }
      } catch (err) {
        console.error('Superset Integration Error:', err);
        setError(err.message || 'Ошибка при загрузке dashboard');
        setLoading(false);
        isEmbedded.current = false;
      }
    };

    loadDashboard();
  }, [dashboardId]);

  return (
    <Box sx={{ position: 'relative', width: '100%', minHeight: '600px' }}>
      {/* Состояние загрузки: отдельный слой поверх контейнера */}
      {loading && !error && (
        <Box 
          sx={{ 
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex', 
            flexDirection: 'column',
            gap: 2,
            justifyContent: 'center', 
            alignItems: 'center',
            zIndex: 10,
            backgroundColor: '#f5f5f5',
            borderRadius: '8px'
          }}
        >
          <CircularProgress />
          <Typography>Загрузка интерактивной аналитики...</Typography>
        </Box>
      )}

      {/* Выделенный контейнер для SDK: React его не трогает после отрисовки */}
      <div
        ref={containerRef}
        style={{ 
          width: '100%', 
          height: '600px', 
          borderRadius: '8px', 
          border: '1px solid #ddd',
          overflow: 'hidden' 
        }}
      />

      {/* Блок ошибок (выводится под графиком, если он есть, или вместо него) */}
      {error && (
        <Box sx={{ p: 2, mt: 2 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          
          <Box sx={{ backgroundColor: '#fff', p: 2, borderRadius: '8px', border: '1px solid #ffcdd2' }}>
            <Typography variant="subtitle1" fontWeight="bold">Инструкция по исправлению:</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              1. Убедитесь, что Docker-контейнеры запущены командой <code>docker-compose up -d</code>.<br />
              2. Проверьте, что в <code>superset_config.py</code> включен <code>ENABLE_CORS = True</code>.<br />
              3. Вставьте актуальный UUID дашборда из настроек Superset.
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default SupersetEmbed;