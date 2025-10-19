# MAHE Innovation Centre - Flask Backend

A comprehensive Flask backend for the MAHE Innovation Centre website with full CRUD operations, API endpoints, and admin panel.

## 🚀 Features

- **RESTful API** for events, resources, contacts, and newsletter
- **Admin Dashboard** for content management
- **Database Models** for events, resources, contacts, and newsletter subscriptions
- **File Upload** support for images and documents
- **Newsletter Management** with subscription/unsubscription
- **Contact Form** handling with admin notifications
- **Production Ready** with deployment configurations

## 📁 Project Structure

```
backend/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── routes.py              # All routes and API endpoints
├── config.py              # Configuration classes
├── wsgi.py                # WSGI entry point
├── requirements.txt       # Python dependencies
├── Procfile               # Heroku deployment
├── runtime.txt            # Python version
├── env_example.txt        # Environment variables template
├── static/
│   └── uploads/           # File upload directory
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Home page
    ├── about.html         # About page
    ├── events.html        # Events page
    ├── resources.html     # Resources page
    ├── contact.html       # Contact page
    └── admin/             # Admin templates
        ├── dashboard.html
        ├── events.html
        ├── resources.html
        ├── contacts.html
        └── newsletter.html
```

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd MIC-website/backend
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp env_example.txt .env
# Edit .env with your configuration
```

### 5. Initialize database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Run the application
```bash
python app.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///mic_innovation.db
FLASK_ENV=development
FLASK_DEBUG=True
```

### Database Configuration

- **Development**: SQLite (default)
- **Production**: PostgreSQL recommended

For PostgreSQL:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/mic_innovation
```

## 📡 API Endpoints

### Events
- `GET /api/events` - Get all events
- `GET /api/events/<id>` - Get specific event
- `POST /api/events` - Create new event

### Resources
- `GET /api/resources` - Get all resources
- `GET /api/resources/<id>` - Get specific resource
- `POST /api/resources/<id>/download` - Download resource

### Contact
- `POST /api/contact` - Submit contact form

### Newsletter
- `POST /api/newsletter` - Subscribe to newsletter
- `DELETE /api/newsletter/<email>` - Unsubscribe from newsletter

## 🎛️ Admin Panel

Access the admin panel at `/admin` with the following features:

- **Dashboard**: Overview of all data
- **Events Management**: Create, edit, delete events
- **Resources Management**: Manage resources and downloads
- **Contact Management**: View and manage contact submissions
- **Newsletter Management**: Manage subscribers

## 🚀 Deployment

### Heroku Deployment

1. **Install Heroku CLI**
2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DATABASE_URL=postgresql://...
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "wsgi:app"]
```

2. **Build and run**
```bash
docker build -t mic-backend .
docker run -p 5000:5000 mic-backend
```

## 📊 Database Models

### Event Model
- `id`, `title`, `description`, `date`, `location`
- `attendees`, `price`, `image_url`, `status`
- `created_at`, `updated_at`

### Resource Model
- `id`, `title`, `description`, `category`
- `file_url`, `download_count`, `rating`
- `format`, `duration`, `is_featured`

### Contact Model
- `id`, `name`, `email`, `subject`, `message`
- `phone`, `company`, `is_read`
- `created_at`

### Newsletter Model
- `id`, `email`, `is_active`
- `subscribed_at`

## 🔒 Security Features

- **CSRF Protection** enabled
- **SQL Injection** protection with SQLAlchemy ORM
- **File Upload** validation and size limits
- **Environment Variables** for sensitive data
- **CORS** configuration for API access

## 📈 Performance Optimizations

- **Database Indexing** on frequently queried fields
- **Connection Pooling** for database connections
- **Static File** serving optimization
- **Caching** for frequently accessed data

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=app tests/
```

## 📝 API Documentation

### Example API Usage

```javascript
// Get all events
fetch('/api/events')
  .then(response => response.json())
  .then(data => console.log(data));

// Subscribe to newsletter
fetch('/api/newsletter', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com'
  })
});

// Submit contact form
fetch('/api/contact', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'John Doe',
    email: 'john@example.com',
    subject: 'Inquiry',
    message: 'Hello, I have a question...'
  })
});
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, email admin@mic.com or create an issue in the repository.
