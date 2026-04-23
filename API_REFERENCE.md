# 🔌 API Reference & Examples

## Backend API (localhost:5000)

### 1. User Registration

**Endpoint:** `POST /api/auth/register`

**Request:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "Password123",
    "confirmPassword": "Password123"
  }'
```

**Response (Success - 201):**
```json
{
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

**Response (Error - 400):**
```json
{
  "message": "User already exists with that email or username"
}
```

**Validation Rules:**
- Username: Minimum 3 characters, must be unique, lowercase
- Email: Valid email format, must be unique
- Password: Minimum 6 characters, must match confirmPassword

---

### 2. User Login

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "Password123"
  }'
```

**Response (Success - 200):**
```json
{
  "message": "Logged in successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "johndoe",
    "email": "john@example.com"
  }
}
```

**Response (Error - 401):**
```json
{
  "message": "Invalid credentials"
}
```

---

### 3. Get Current User (Protected)

**Endpoint:** `GET /api/auth/me`

**Required Header:**
```
Authorization: Bearer <jwt_token>
```

**Request:**
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (Success - 200):**
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "johndoe",
    "email": "john@example.com",
    "createdAt": "2024-04-16T10:30:00.000Z"
  }
}
```

**Response (Error - 401):**
```json
{
  "message": "Invalid token"
}
```

---

### 4. Health Check

**Endpoint:** `GET /health`

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "message": "Server is running"
}
```

---

## ML Model API (localhost:5001)

### 1. Single Text Prediction

**Endpoint:** `POST /api/predict`

**Request:**
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Click here urgently to verify your Amazon account! Wire $500 immediately!"
  }'
```

**Response (Success - 200):**
```json
{
  "success": true,
  "prediction": {
    "classification": "scam",
    "confidence": 0.92,
    "scam_score": 0.85,
    "insights": [
      "Contains 'click here' - common in phishing attacks",
      "Contains 'urgently' - pressure tactic",
      "Contains 'verify' - common in scam pattern",
      "Contains 'wire' - money transfer request",
      "Contains 'immediately' - pressure tactic"
    ]
  },
  "text": "Click here urgently to verify your Amazon account! Wire $..."
}
```

**Response (Error - 400):**
```json
{
  "error": "Missing text field",
  "message": "Please provide text to analyze"
}
```

**Classification Values:**
- `"scam"` - High confidence it's a scam (≥70% score)
- `"suspicious"` - Needs caution (40-69% score)
- `"not_a_scam"` - Appears legitimate (<40% score)

---

### 2. Batch Predictions

**Endpoint:** `POST /api/batch-predict`

**Request:**
```bash
curl -X POST http://localhost:5001/api/batch-predict \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Verify your account urgently!",
      "Hello, meeting tomorrow at 3 PM",
      "Click to claim prize money!"
    ]
  }'
```

**Response (Success - 200):**
```json
{
  "success": true,
  "predictions": [
    {
      "text": "Verify your account urgently!",
      "prediction": {
        "classification": "suspicious",
        "confidence": 0.65,
        "scam_score": 0.55,
        "insights": [
          "Contains 'verify' - common verification scam",
          "Contains 'urgently' - pressure tactic"
        ]
      }
    },
    {
      "text": "Hello, meeting tomorrow at 3 PM",
      "prediction": {
        "classification": "not_a_scam",
        "confidence": 0.95,
        "scam_score": 0.05,
        "insights": []
      }
    },
    {
      "text": "Click to claim prize money!",
      "prediction": {
        "classification": "scam",
        "confidence": 0.88,
        "scam_score": 0.78,
        "insights": [
          "Contains 'click' - phishing indicator",
          "Contains 'prize money' - false promise",
          "Contains 'claim' - false reward"
        ]
      }
    }
  ],
  "count": 3
}
```

**Limits:**
- Maximum 10 texts per batch
- Total text character limit: 10,000 characters

---

### 3. Health Check

**Endpoint:** `GET /api/health`

**Request:**
```bash
curl http://localhost:5001/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "ML Model API is running"
}
```

---

## JavaScript/Fetch Examples

### Register User (JavaScript)

```javascript
async function registerUser(username, email, password) {
  try {
    const response = await fetch('http://localhost:5000/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        email,
        password,
        confirmPassword: password
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Registration failed');
    }

    // Store token
    localStorage.setItem('token', data.token);
    console.log('Registration successful!', data.user);
    return data;
  } catch (error) {
    console.error('Registration error:', error.message);
  }
}
```

---

### Login User (JavaScript)

```javascript
async function loginUser(email, password) {
  try {
    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Login failed');
    }

    // Store token
    localStorage.setItem('token', data.token);
    console.log('Login successful!', data.user);
    return data;
  } catch (error) {
    console.error('Login error:', error.message);
  }
}
```

---

### Get Current User (JavaScript)

```javascript
async function getCurrentUser() {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No token found');
    }

    const response = await fetch('http://localhost:5000/api/auth/me', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to get user');
    }

    console.log('Current user:', data.user);
    return data.user;
  } catch (error) {
    console.error('Error getting user:', error.message);
  }
}
```

---

### Analyze Text (JavaScript)

```javascript
async function analyzeText(text) {
  try {
    if (!text.trim()) {
      throw new Error('Text cannot be empty');
    }

    const response = await fetch('http://localhost:5001/api/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Analysis failed');
    }

    console.log('Analysis result:', data.prediction);
    return data.prediction;
  } catch (error) {
    console.error('Analysis error:', error.message);
  }
}
```

---

## Python Examples

### Test Backend API (Python)

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Register
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPassword123",
    "confirmPassword": "TestPassword123"
}

response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
print("Register:", response.json())

# Extract token
token = response.json().get('token')

# Get current user (protected)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
print("Current user:", response.json())

# Login
login_data = {
    "email": "test@example.com",
    "password": "TestPassword123"
}

response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
print("Login:", response.json())
```

---

### Test ML Model API (Python)

```python
import requests

ML_URL = "http://localhost:5001"

# Single prediction
text_data = {
    "text": "Click here urgently to verify your account and wire money!"
}

response = requests.post(f"{ML_URL}/api/predict", json=text_data)
result = response.json()
print("Prediction:")
print(f"  Classification: {result['prediction']['classification']}")
print(f"  Confidence: {result['prediction']['confidence']:.2%}")
print(f"  Insights: {result['prediction']['insights']}")

# Batch prediction
batch_data = {
    "texts": [
        "Verify account urgently!",
        "Meeting tomorrow",
        "Claim your prize money!"
    ]
}

response = requests.post(f"{ML_URL}/api/batch-predict", json=batch_data)
results = response.json()
print(f"\nBatch results: {len(results['predictions'])} texts analyzed")
```

---

## Error Codes Reference

| Code | Status | Message | Solution |
|------|--------|---------|----------|
| 200 | OK | Success | Request succeeded |
| 201 | Created | Resource created | User registered |
| 400 | Bad Request | Missing/invalid data | Check request format |
| 401 | Unauthorized | Invalid credentials/token | Check email/password or token |
| 404 | Not Found | Endpoint not found | Check URL |
| 500 | Server Error | Server error | Check server logs |

---

## Rate Limiting Notes

**Current**: No rate limiting implemented

**For Production**: Add rate limiting middleware:
- 100 requests/minute for auth endpoints
- 1000 requests/minute for ML endpoint
- Prevent brute force attacks

---

## Authentication Flow

```
1. User sends email + password
   ↓
2. Backend validates credentials
   ↓
3. Password compared with hash
   ↓
4. JWT token generated
   ↓
5. Token returned to frontend
   ↓
6. Token stored in localStorage
   ↓
7. Token sent in Authorization header for protected requests
   ↓
8. Middleware verifies token validity
```

---

## Token Structure (JWT)

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "userId": "507f1f77bcf86cd799439011",
  "iat": 1713273000,
  "exp": 1713878000
}
```

**Expiration:** 7 days from creation

---

## Postman Setup

### Import Collection

1. Open Postman
2. Create new collection: "FinShield"
3. Add requests:

**Auth Requests:**
- POST: Register → `http://localhost:5000/api/auth/register`
- POST: Login → `http://localhost:5000/api/auth/login`
- GET: Me → `http://localhost:5000/api/auth/me`

**ML Requests:**
- POST: Predict → `http://localhost:5001/api/predict`
- POST: Batch → `http://localhost:5001/api/batch-predict`
- GET: Health → `http://localhost:5001/api/health`

### Authentication Setup

1. Go to Auth tab
2. Select "Bearer Token"
3. Paste your JWT token
4. Applies to all requests in collection

---

## CORS Configuration

**Current Setup:**
- Frontend: `http://localhost:3000` ✅
- Backend CORS: Allows localhost:3000
- ML CORS: Allows all origins (*)

**Production Changes:**
- Specify exact frontend domain
- Remove wildcard CORS
- Use environment variables

---

## Testing Commands Reference

```bash
# Test backend is running
curl http://localhost:5000/health

# Test ML server is running
curl http://localhost:5001/api/health

# Test registration
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123","confirmPassword":"pass123"}'

# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123"}'

# Test ML prediction
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Click here urgently to verify your account!"}'
```

---

**All endpoints are ready to use! Happy testing! 🚀**
