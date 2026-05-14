import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';

const PlayerAnalysis = () => {
  const [playerName, setPlayerName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [playerData, setPlayerData] = useState(null);
  const [recommendations, setRecommendations] = useState(null);

  const handleSearch = async () => {
    if (!playerName.trim()) {
      setError('Введите имя игрока');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // TODO: Замените на реальный API endpoint
      const response = await fetch(`http://localhost:8000/api/players/search?name=${playerName}`);
      
      if (response.ok) {
        const data = await response.json();
        setPlayerData(data);
      } else if (response.status === 404) {
        setError('Игрок не найден');
      } else {
        setError('Ошибка при поиске игрока');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGetRecommendations = async (playerId) => {
    try {
      setLoading(true);
      
      // TODO: Замените на реальный API endpoint
      const response = await fetch(`http://localhost:8000/api/players/${playerId}/recommendations`);
      
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (err) {
      setError('Ошибка при получении рекомендаций');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        🔍 Анализ игрока
      </Typography>

      {/* Форма поиска */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Имя игрока"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              disabled={loading}
              fullWidth
              placeholder="Например: Marcus Rashford"
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              sx={{ whiteSpace: 'nowrap' }}
            >
              {loading ? <CircularProgress size={24} /> : 'Поиск'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Результаты поиска */}
      {playerData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Информация об игроке
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 2 }}>
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Typography color="textSecondary">Имя</Typography>
                <Typography variant="h6">{playerData.player_name}</Typography>
              </Paper>
              
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Typography color="textSecondary">Позиция</Typography>
                <Typography variant="h6">{playerData.position}</Typography>
              </Paper>
              
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Typography color="textSecondary">Команда</Typography>
                <Typography variant="h6">{playerData.team_name}</Typography>
              </Paper>
              
              <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <Typography color="textSecondary">Роль</Typography>
                <Typography variant="h6" sx={{ color: '#9c27b0' }}>
                  {playerData.role_name}
                </Typography>
              </Paper>
            </Box>

            <Button
              variant="contained"
              color="primary"
              onClick={() => handleGetRecommendations(playerData.player_id)}
              disabled={loading}
            >
              Получить рекомендации упражнений
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Рекомендации */}
      {recommendations && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              💪 Рекомендуемые упражнения
            </Typography>

            {recommendations.deficits && recommendations.deficits.length > 0 && (
              <>
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Дефицитные метрики:
                </Typography>
                <TableContainer component={Paper} sx={{ mb: 3 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell>Метрика</TableCell>
                        <TableCell align="right">Z-score</TableCell>
                        <TableCell align="right">Факт</TableCell>
                        <TableCell align="right">Норма</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recommendations.deficits.map((deficit, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{deficit.metric_name}</TableCell>
                          <TableCell align="right" sx={{ color: deficit.z_score < -2 ? '#f44336' : '#ff9800' }}>
                            {deficit.z_score.toFixed(2)}
                          </TableCell>
                          <TableCell align="right">{deficit.actual.toFixed(2)}</TableCell>
                          <TableCell align="right">{deficit.mean.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {recommendations.exercises && recommendations.exercises.length > 0 && (
              <>
                <Typography variant="subtitle2" gutterBottom>
                  Упражнения ({recommendations.exercises.length}):
                </Typography>
                <Box sx={{ display: 'grid', gap: 2 }}>
                  {recommendations.exercises.map((exercise, idx) => (
                    <Paper key={idx} sx={{ p: 2, borderLeft: '4px solid #1976d2' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {exercise.exercise_name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        {exercise.exercise_description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, fontSize: '0.9em' }}>
                        <span>📌 Метрика: <strong>{exercise.metric_name}</strong></span>
                        <span>🎯 Сложность: <strong>{exercise.difficulty}/10</strong></span>
                      </Box>
                    </Paper>
                  ))}
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PlayerAnalysis;
