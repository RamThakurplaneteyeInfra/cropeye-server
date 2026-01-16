# 🌾 Farm Management System

A comprehensive Django-based farm management system with GIS capabilities, user management, and RESTful APIs.

## 🚀 Features

- **User Management**: Role-based access control (Admin, Field Officer, Farmer)
- **Farm Management**: Complete farm registration and management
- **GIS Integration**: Plot mapping with PostGIS and Leaflet
- **Irrigation Management**: Drip and flood irrigation tracking
- **Task Management**: Assignment and tracking of agricultural tasks
- **Equipment Management**: Farm equipment inventory and booking
- **RESTful APIs**: Comprehensive API endpoints with JWT authentication
- **Real-time Updates**: WebSocket support for live updates
- **Performance Monitoring**: Built-in performance testing and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API    │    │   PostgreSQL    │
│   (React/Vue)   │◄──►│   (REST/WS)     │◄──►│   + PostGIS     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   FastAPI       │
                       │   Services      │
                       └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Django 5.0.1, Django REST Framework
- **Database**: PostgreSQL with PostGIS extension
- **GIS**: GeoDjango, Leaflet, Shapely
- **Authentication**: JWT (Simple JWT)
- **API Documentation**: Swagger/OpenAPI
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx, Gunicorn
- **Monitoring**: Custom performance testing suite

## 📋 Prerequisites

- Python 3.12+
- PostgreSQL 15+ with PostGIS
- Docker & Docker Compose (for containerized deployment)
- Git

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd farm-management-system
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Deploy with Docker**
   ```bash
   ./deploy.sh
   ```

4. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Swagger: http://localhost:8000/swagger/

### Option 2: Manual Installation

1. **Create virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_production.txt
   ```

3. **Set up database**
   ```bash
   # Create PostgreSQL database with PostGIS
   createdb farm_management
   psql farm_management -c "CREATE EXTENSION postgis;"
   ```

4. **Configure environment**
   ```bash
   export DJANGO_SETTINGS_MODULE=farm_management.settings_production
   export SECRET_KEY=your-secret-key
   export DATABASE_URL=postgresql://user:password@localhost:5432/farm_management
   ```

5. **Run migrations and start server**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py runserver
   ```

## 📁 Project Structure

```
farm-management-system/
├── farm_management/          # Django project settings
├── users/                   # User management app
├── farms/                   # Farm management app
├── tasks/                   # Task management app
├── equipment/               # Equipment management app
├── bookings/                # Booking management app
├── inventory/               # Inventory management app
├── vendors/                 # Vendor management app
├── media/                   # Media files
├── staticfiles/             # Static files
├── templates/               # HTML templates
├── ui/                      # Frontend UI files
├── testing/                 # Testing scripts and documentation (excluded from production)
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── nginx.conf               # Nginx configuration
├── requirements.txt         # Development dependencies
├── requirements_production.txt # Production dependencies
├── deploy.sh                # Deployment script
└── DEPLOYMENT.md            # Detailed deployment guide
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | Required |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | Required |
| `EMAIL_HOST_PASSWORD` | SMTP password | Required |

### Database Configuration

The system uses PostgreSQL with PostGIS for GIS functionality:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'farm_management',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔐 Authentication & Authorization

### User Roles

1. **Admin**: Full system access
2. **Field Officer**: Farm management and farmer oversight
3. **Farmer**: Farm and plot management

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}
```

## 📊 API Endpoints

### Authentication
- `POST /api/token/` - Get JWT tokens
- `POST /api/token/refresh/` - Refresh access token

### Users
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/me/` - Update user profile

### Farms
- `GET /api/farms/` - List farms
- `POST /api/farms/` - Create farm
- `GET /api/farms/{id}/` - Get farm details
- `PUT /api/farms/{id}/` - Update farm
- `DELETE /api/farms/{id}/` - Delete farm

### Tasks
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/{id}/` - Get task details
- `PUT /api/tasks/{id}/` - Update task

### Equipment
- `GET /api/equipment/` - List equipment
- `POST /api/equipment/` - Create equipment
- `GET /api/equipment/{id}/` - Get equipment details

### Bookings
- `GET /api/bookings/` - List bookings
- `POST /api/bookings/` - Create booking
- `GET /api/bookings/{id}/` - Get booking details

## 🧪 Testing

### Performance Testing

The system includes comprehensive performance testing:

```bash
# Run performance tests
python performance_test.py

# View performance dashboard
open performance_dashboard.html
```

### API Testing

```bash
# Test API endpoints
python test_auth.py
python test_farm_api.py
python test_manager_api.py
```

## 📈 Performance Metrics

Based on performance testing:

- **Database Queries**: < 20ms average
- **API Response Time**: < 100ms average
- **Concurrent Requests**: 10+ requests/second
- **Memory Usage**: < 50MB base usage
- **Success Rate**: 99.9% under normal load

## 🔒 Security Features

- JWT-based authentication
- Role-based access control
- CORS protection
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting
- Input validation

## 📱 Frontend Integration

The system provides RESTful APIs that can be integrated with any frontend framework:

### React Example
```javascript
// Login
const response = await fetch('/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

// Get farms
const farms = await fetch('/api/farms/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### Vue.js Example
```javascript
// Using axios
const api = axios.create({
  baseURL: '/api/',
  headers: { 'Authorization': `Bearer ${token}` }
});

// Get user profile
const profile = await api.get('/users/me/');
```

## 🚀 Deployment

### Production Deployment

1. **Server Requirements**
   - Ubuntu 20.04+ or CentOS 8+
   - 2GB RAM minimum
   - 20GB storage
   - Docker and Docker Compose

2. **SSL Certificate**
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. **Environment Setup**
   ```bash
   export SECRET_KEY=your-production-secret-key
   export DEBUG=False
   export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

4. **Deploy**
   ```bash
   ./deploy.sh
   ```

### Cloud Deployment

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway deploy
```

#### Heroku
```bash
# Install Heroku CLI
# Create Procfile
echo "web: gunicorn farm_management.wsgi:application" > Procfile

# Deploy
git push heroku main
```

## 📊 Monitoring

### Health Checks
- Database connectivity
- API endpoint availability
- Memory usage
- Response times

### Logging
- Application logs
- Error tracking
- Performance metrics
- Security events

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the deployment guide

## 🔄 Updates

### Version History
- v1.0.0 - Initial release
- v1.1.0 - Added GIS functionality
- v1.2.0 - Performance improvements
- v1.3.0 - Docker deployment support

### Upcoming Features
- Mobile app integration
- Advanced analytics
- IoT device integration
- Machine learning predictions

---

**Built with ❤️ for modern agriculture**