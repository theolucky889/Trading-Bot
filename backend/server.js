// ─────────────────────────────────────────────────────────────────────
// LEGACY / OPTIONAL — MongoDB-based auth server.
//
// Auth (register / login / session + per-user sentiment history) is now
// served by the FastAPI app on :8000 (backend/auth.py, SQLite). This Express
// server is NO LONGER wired to the Vite dev proxy and is not required to run
// the app. It is retained only as an optional MongoDB-backed alternative.
// Do not add new functionality here — extend backend/auth.py instead.
// ─────────────────────────────────────────────────────────────────────

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');
const rateLimit = require('express-rate-limit');

// Minimum password length. Mirror this in the client (RegisterView.vue).
const MIN_PASSWORD_LENGTH = 8;

// Basic email format check (server-side; the client also validates).
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const app = express();

// ── Environment-based configuration ──────────────────────────────────
const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/trading-bot';
const SECRET_KEY = process.env.JWT_SECRET;

// Fail fast if the JWT secret is not configured — never fall back to a
// hardcoded secret (anyone could then mint valid tokens).
if (!SECRET_KEY) {
  console.error(
    'FATAL: JWT_SECRET environment variable is not set. ' +
      'Set a strong secret (see backend/.env.example) before starting the auth server.'
  );
  process.exit(1);
}

// Use the CORS middleware
app.use(cors());

// Middleware to parse JSON bodies
app.use(bodyParser.json());

// Rate limiter for authentication attempts — mitigate brute-forcing /api/login.
// Configurable via env; defaults to 10 attempts per 15 minutes per IP.
const loginLimiter = rateLimit({
  windowMs: parseInt(process.env.LOGIN_RATE_WINDOW_MS || '', 10) || 15 * 60 * 1000,
  max: parseInt(process.env.LOGIN_RATE_MAX || '', 10) || 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { message: 'Too many login attempts. Please try again later.' },
});

// Connect to MongoDB — handle rejection instead of silently starting broken.
mongoose
  .connect(MONGODB_URI)
  .then(() => console.log(`Connected to MongoDB at ${MONGODB_URI}`))
  .catch((err) => {
    console.error('FATAL: could not connect to MongoDB:', err.message);
    process.exit(1);
  });

// Define a User schema
const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
});

// Create a User model
const User = mongoose.model('User', userSchema);

// Sentiment search history (per user)
const sentimentHistorySchema = new mongoose.Schema({
  email: { type: String, required: true, index: true },
  query: { type: String, required: true },
  numArticles: { type: Number },
  model: { type: String },
  avgCompound: { type: Number },
  createdAt: { type: Date, default: Date.now },
});

const SentimentHistory = mongoose.model('SentimentHistory', sentimentHistorySchema);

// Middleware to verify token
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) return res.sendStatus(401);

  // Strip the "Bearer " prefix before verifying.
  const token = authHeader.startsWith('Bearer ')
    ? authHeader.slice('Bearer '.length).trim()
    : authHeader;

  if (!token) return res.sendStatus(401);

  jwt.verify(token, SECRET_KEY, (err, user) => {
    if (err) return res.sendStatus(403);
    req.user = user;
    next();
  });
}

// Registration endpoint
app.post('/api/register', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required' });
  }

  if (!EMAIL_RE.test(String(email).trim())) {
    return res.status(400).json({ message: 'Please enter a valid email address.' });
  }

  if (String(password).length < MIN_PASSWORD_LENGTH) {
    return res
      .status(400)
      .json({ message: `Password must be at least ${MIN_PASSWORD_LENGTH} characters.` });
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({ email, password: hashedPassword });
    await user.save();
    res.status(201).json({ message: 'Registration successful' });
  } catch (error) {
    if (error.code === 11000) {
      res.status(409).json({ message: 'User already exists' });
    } else {
      res.status(500).json({ message: 'Internal server error' });
    }
  }
});

// Login endpoint (rate-limited to slow brute-force attempts)
app.post('/api/login', loginLimiter, async (req, res) => {
  const { email, password } = req.body;

  try {
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(404).json({ message: 'Account not registered. Please register first.' });
    }

    if (await bcrypt.compare(password, user.password)) {
      const token = jwt.sign({ email: user.email }, SECRET_KEY, { expiresIn: '1h' });
      return res.status(200).json({ message: 'Login successful', token });
    } else {
      return res.status(401).json({ message: 'Invalid password' });
    }
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// ── Sentiment search history (per user) ──────────────────────────────

// List the current user's recent searches (most recent first, cap 20).
app.get('/api/sentiment/history', authenticateToken, async (req, res) => {
  try {
    const items = await SentimentHistory.find({ email: req.user.email })
      .sort({ createdAt: -1 })
      .limit(20)
      .lean();
    res.status(200).json(items);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Save a search run for the current user.
app.post('/api/sentiment/history', authenticateToken, async (req, res) => {
  const { query, numArticles, model, avgCompound } = req.body;

  if (!query || typeof query !== 'string' || !query.trim()) {
    return res.status(400).json({ message: 'query is required' });
  }

  try {
    const record = new SentimentHistory({
      email: req.user.email,
      query: query.trim(),
      numArticles: typeof numArticles === 'number' ? numArticles : undefined,
      model: typeof model === 'string' ? model : undefined,
      avgCompound: typeof avgCompound === 'number' ? avgCompound : undefined,
    });
    await record.save();
    res.status(201).json(record.toObject());
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
