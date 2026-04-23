# Backend - Authentication System

This is the backend API for user authentication with MongoDB and Express.

## Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure Environment Variables**
   Edit `.env` file with your settings:
   - `MONGO_URI`: MongoDB connection string (default: `mongodb://localhost:27017/majorproject`)
   - `JWT_SECRET`: Secret key for JWT (change in production)
   - `PORT`: Server port (default: 5000)

3. **Start MongoDB**
   Make sure MongoDB is running on your system.

4. **Run the Server**
   - Development mode (with auto-reload):
     ```bash
     npm run dev
     ```
   - Production mode:
     ```bash
     npm start
     ```

## API Endpoints

### Authentication Routes (`/api/auth`)

#### Register User
- **POST** `/api/auth/register`
- **Body:**
  ```json
  {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "password123",
    "confirmPassword": "password123"
  }
  ```
- **Response:**
  ```json
  {
    "message": "User registered successfully",
    "token": "jwt_token_here",
    "user": {
      "id": "user_id",
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
  ```

#### Login User
- **POST** `/api/auth/login`
- **Body:**
  ```json
  {
    "email": "john@example.com",
    "password": "password123"
  }
  ```
- **Response:**
  ```json
  {
    "message": "Logged in successfully",
    "token": "jwt_token_here",
    "user": {
      "id": "user_id",
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
  ```

#### Get Current User (Protected Route)
- **GET** `/api/auth/me`
- **Headers:**
  ```
  Authorization: Bearer <jwt_token>
  ```
- **Response:**
  ```json
  {
    "user": {
      "id": "user_id",
      "username": "johndoe",
      "email": "john@example.com",
      "createdAt": "2024-01-01T00:00:00.000Z"
    }
  }
  ```

## Project Structure

```
backend/
├── index.js           # Main server file
├── config.js          # Database configuration
├── .env              # Environment variables
├── package.json      # Dependencies
├── models/
│   └── User.js       # User schema and model
├── routes/
│   └── auth.js       # Authentication routes
└── middleware/
    └── auth.js       # JWT authentication middleware
```

## Features

- User registration with validation
- User login with JWT authentication
- Password hashing with bcryptjs
- Protected routes using JWT middleware
- CORS support for frontend communication
- MongoDB integration with Mongoose
- Environment-based configuration

## Database Schema (User)

```javascript
{
  username: String (unique, lowercase, min 3 chars),
  email: String (unique, lowercase, valid email),
  password: String (hashed, min 6 chars),
  createdAt: Date (auto-generated)
}
```

## Security Notes

1. Change `JWT_SECRET` in production
2. Use HTTPS in production
3. Implement rate limiting for login/register endpoints
4. Store sensitive data in environment variables
5. Validate all user inputs

## Installation Requirements

- Node.js (v14 or higher)
- MongoDB (local or cloud - MongoDB Atlas)
- npm or yarn

## Dependencies

- **express**: Web framework
- **mongoose**: MongoDB ODM
- **bcryptjs**: Password hashing
- **jsonwebtoken**: JWT creation and verification
- **dotenv**: Environment variable management
- **cors**: Cross-origin resource sharing
- **nodemon**: Auto-reload development server
