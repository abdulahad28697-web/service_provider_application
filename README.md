# ServiceHub AI

ServiceHub AI is a full-stack service provider and booking platform that connects customers with verified service providers.

The platform supports customer bookings, provider management, messaging, reviews, notifications, payments, AI assistance, and admin management.

## Features

### Customer Features

- User registration and login
- JWT authentication
- Profile management
- Address management
- Browse services
- Search and filter services
- Provider public profiles
- Favorite providers
- Booking creation
- Provider availability and time-slot selection
- Booking history
- Booking cancellation
- Booking rescheduling
- Customer-provider messaging
- Notifications
- Payment checkout
- Cash, JazzCash and Easypaisa payment options
- Reviews and ratings
- AI service assistant

### Provider Features

- Provider onboarding
- Provider profile management
- Service creation and management
- Provider availability management
- Booking request management
- Accept, reject and complete bookings
- Customer messaging
- Notifications
- Payment status tracking
- Cash payment confirmation
- Earnings and revenue dashboard
- Portfolio management
- Reviews and ratings

### Admin Features

- Admin authentication
- Admin dashboard
- Provider verification
- Provider application management
- Booking management
- Review management
- Payment management
- Active/deactivated user statistics
- Audit logs

## Technology Stack

### Frontend

- React
- Vite
- React Router
- Axios
- Lucide React
- CSS

### Backend

- FastAPI
- Python
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT Authentication
- AsyncPG
- Redis

### Infrastructure

- Docker
- Docker Compose
- PostgreSQL
- Redis

## Project Structure

```text
service-provider-team/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── .env.example
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── .gitignore
├── docker-compose.yml
└── README.md