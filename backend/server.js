const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'your_secret_key'; // Use a strong secret key

// Use the CORS middleware
app.use(cors());

// Middleware to parse JSON bodies
app.use(bodyParser.json());

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/trading-bot', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Define a User schema
const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
});

// Create a User model
const User = mongoose.model('User', userSchema);

// Registration endpoint
app.post('/api/register', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required' });
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

// Login endpoint
app.post('/api/login', async (req, res) => {
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

// Middleware to verify token
function authenticateToken(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.sendStatus(401);

  jwt.verify(token, SECRET_KEY, (err, user) => {
    if (err) return res.sendStatus(403);
    req.user = user;
    next();
  });
}

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
