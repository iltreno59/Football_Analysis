import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Container, Box, CssBaseline } from '@mui/material';
import './App.css';
import Dashboard from './pages/Dashboard';
import PlayerAnalysis from './pages/PlayerAnalysis';
import Reports from './pages/Reports';

function App() {
  return (
    <Router>
      <CssBaseline />
      <AppBar position="static" sx={{ backgroundColor: '#1976d2' }}>
        <Toolbar>
          <Box sx={{ flexGrow: 1, display: 'flex', gap: 2 }}>
            <Link to="/" style={{ color: 'white', textDecoration: 'none', fontSize: '1.2em' }}>
              ⚽ Football Analysis
            </Link>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>Dashboard</Link>
            <Link to="/players" style={{ color: 'white', textDecoration: 'none' }}>Players</Link>
            <Link to="/reports" style={{ color: 'white', textDecoration: 'none' }}>Reports</Link>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/players" element={<PlayerAnalysis />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
