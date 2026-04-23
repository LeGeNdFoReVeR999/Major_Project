const express = require('express');
const cors = require('cors');
require('dotenv').config();

const connectDB = require('./config');
const authRoutes = require('./routes/auth');
const searchHistoryRoutes = require('./routes/searchHistory');

const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true
}));

// Connect to database
connectDB();

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/search-history', searchHistoryRoutes);

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({ message: 'Server is running' });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Internal server error', error: err.message });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Visit http://localhost:${PORT}/health to check server status`);
});
