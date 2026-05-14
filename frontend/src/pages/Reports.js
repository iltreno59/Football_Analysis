import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Chip,
  Grid
} from '@mui/material';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      // TODO: Замените на реальный API endpoint
      const response = await fetch('http://localhost:8000/api/reports');
      
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      } else {
        setError('Ошибка при загрузке отчётов');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
      console.error(err);
      // Временные данные для демонстрации
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (reportId) => {
    try {
      // TODO: Замените на реальный API endpoint
      const response = await fetch(`http://localhost:8000/api/reports/${reportId}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedReport(data);
        setOpenDialog(true);
      }
    } catch (err) {
      console.error('Error fetching report details:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        📋 Отчёты
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {reports.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="textSecondary">
              Отчётов не найдено. Создайте первый отчёт на странице "Players".
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                <TableCell>Игрок</TableCell>
                <TableCell>Позиция</TableCell>
                <TableCell>Команда</TableCell>
                <TableCell>Дата создания</TableCell>
                <TableCell align="center">Упражнений</TableCell>
                <TableCell align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.report_id} hover>
                  <TableCell sx={{ fontWeight: 'bold' }}>
                    {report.player_name}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={report.position}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{report.team_name}</TableCell>
                  <TableCell>
                    {format(new Date(report.created_at), 'dd MMMM yyyy HH:mm', { locale: ru })}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={report.exercise_count || 0}
                      size="small"
                      color={report.exercise_count > 0 ? 'primary' : 'default'}
                      variant="filled"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleViewDetails(report.report_id)}
                    >
                      Просмотр
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dialog с деталями отчёта */}
      {selectedReport && (
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            Отчёт: {selectedReport.player_name}
          </DialogTitle>
          <DialogContent sx={{ py: 2 }}>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  Игрок
                </Typography>
                <Typography variant="body1">
                  {selectedReport.player_name}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  Команда
                </Typography>
                <Typography variant="body1">
                  {selectedReport.team_name}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  Роль
                </Typography>
                <Typography variant="body1" sx={{ color: '#9c27b0' }}>
                  {selectedReport.role_name}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="textSecondary">
                  Дата создания
                </Typography>
                <Typography variant="body1">
                  {format(new Date(selectedReport.created_at), 'dd MMMM yyyy HH:mm', { locale: ru })}
                </Typography>
              </Grid>
            </Grid>

            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Рекомендуемые упражнения
            </Typography>

            {selectedReport.exercises && selectedReport.exercises.length > 0 ? (
              <Box sx={{ display: 'grid', gap: 1.5 }}>
                {selectedReport.exercises.map((exercise, idx) => (
                  <Paper key={idx} sx={{ p: 1.5, borderLeft: '4px solid #1976d2' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {exercise.exercise_name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {exercise.exercise_description}
                        </Typography>
                      </Box>
                      <Chip
                        label={`Сложность: ${exercise.difficulty}`}
                        size="small"
                        color={exercise.difficulty > 7 ? 'error' : 'default'}
                      />
                    </Box>
                  </Paper>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Упражнений не найдено
              </Typography>
            )}
          </DialogContent>
        </Dialog>
      )}
    </Box>
  );
};

export default Reports;
