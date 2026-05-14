import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  Alert
} from '@mui/material';
import SupersetEmbed from '../components/SupersetEmbed';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalPlayers: 0,
    totalRoles: 0,
    totalReports: 0
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      // TODO: Замените на реальный API endpoint
      const response = await fetch('http://localhost:8000/api/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('Не удалось загрузить статистику');
      // Используем временные данные для демонстрации
      setStats({
        totalPlayers: 400,
        totalRoles: 16,
        totalReports: 5
      });
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      {/* Заголовок */}
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        📊 Dashboard
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Статистика */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#e3f2fd' }}>
            <Typography variant="h6" color="textSecondary">Всего игроков</Typography>
            <Typography variant="h3" sx={{ color: '#1976d2', mt: 1 }}>
              {stats.totalPlayers}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f3e5f5' }}>
            <Typography variant="h6" color="textSecondary">Ролей найдено</Typography>
            <Typography variant="h3" sx={{ color: '#9c27b0', mt: 1 }}>
              {stats.totalRoles}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#e8f5e9' }}>
            <Typography variant="h6" color="textSecondary">Отчётов создано</Typography>
            <Typography variant="h3" sx={{ color: '#4caf50', mt: 1 }}>
              {stats.totalReports}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Основная информация */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            ℹ️ О системе
          </Typography>
          <Typography variant="body1" paragraph>
            Система анализа ролей футболистов использует машинное обучение для определения 
            стилистических характеристик игроков. На основе кластеризации создаются 16 различных ролей:
          </Typography>
          <Typography variant="body2" component="div" sx={{ ml: 2 }}>
            • <strong>GK (1-3):</strong> Вратари (распределение, претензии)<br />
            • <strong>CB (1-3):</strong> Центральные защитники (воздушная игра, передачи)<br />
            • <strong>FB (1-3):</strong> Фланговые защитники (фланги, защита)<br />
            • <strong>CM (1-5):</strong> Полузащитники (защита, атака, креатив)<br />
            • <strong>WG (1-3):</strong> Вингеры (дриблинг, удары)<br />
            • <strong>ST (1-4):</strong> Нападающие (финиш, объём)<br />
          </Typography>
        </CardContent>
      </Card>

      {/* Embedded Superset Dashboard */}
      <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
        📈 Интерактивная аналитика
      </Typography>
      <Paper sx={{ p: 2, bgcolor: '#f9f9f9', minHeight: 600 }}>
        <SupersetEmbed />
      </Paper>
    </Box>
  );
};

export default Dashboard;
