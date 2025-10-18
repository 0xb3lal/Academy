# Raven Academy - Online Learning Platform

A comprehensive web-based learning management system built with Flask, featuring course management, lesson creation, user authentication, and administrative controls.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Security Features](#security-features)
- [Contributing](#contributing)
- [License](#license)

## Features

### User Management
- User registration and authentication
- Profile management with image uploads
- Password reset functionality with email verification
- Role-based access control (Admin/User)
- Rate limiting for password reset requests

### Course Management
- Create and manage courses
- Course categorization and organization
- Course icons and descriptions
- Course enrollment tracking

### Lesson System
- Rich text editor (CKEditor) for lesson content
- Lesson thumbnails and metadata
- Course-lesson relationships
- Author attribution and management

### Administrative Panel
- Comprehensive admin dashboard
- User management and statistics
- Course and lesson administration
- System analytics and reporting
- Bulk operations and data export

### Security Features
- Bcrypt password hashing
- CSRF protection
- SQL injection prevention
- Rate limiting
- Secure session management
- Email verification system

## Technology Stack

### Backend
- **Flask 2.3.3** - Web framework
- **SQLAlchemy 2.0.44** - ORM and database management
- **Flask-Login 0.6.3** - User session management
- **Flask-Bcrypt 1.0.1** - Password hashing
- **Flask-WTF 1.2.1** - Form handling and CSRF protection
- **Flask-Mail 0.10.0** - Email functionality
- **Flask-Migrate 4.1.0** - Database migrations

### Frontend
- **Bootstrap 5.1.3** - CSS framework
- **Font Awesome 6.0.0** - Icons
- **CKEditor** - Rich text editor
- **Custom CSS** - Brand-specific styling

### Database
- **SQLite** (default) - Development database
- **PostgreSQL/MySQL** - Production ready

### Additional Tools
- **Pillow 11.3.0** - Image processing
- **python-dotenv 1.1.1** - Environment variable management
- **bleach 6.2.0** - HTML sanitization
- **email-validator 2.3.0** - Email validation

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/raven_project.git
cd raven_project
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the project root:
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```env
# Email Configuration
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

# Security
SECRET_KEY=your_secret_key_here

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite:///site.db
```

### Step 5: Database Setup
```bash
# Initialize database
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

### Step 6: Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Generated key |
| `DATABASE_URL` | Database connection string | `sqlite:///site.db` |
| `EMAIL_USER` | Gmail username for sending emails | Required |
| `EMAIL_PASS` | Gmail app password | Required |
| `MAIL_DEFAULT_SENDER` | Default sender email | Required |

### Email Configuration
To enable email functionality:
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password
3. Use the App Password in `EMAIL_PASS`

## Usage

### For Students
1. Register a new account
2. Browse available courses
3. Access lesson content
4. Update profile information

### For Instructors
1. Create courses with descriptions and icons
2. Add lessons with rich text content
3. Upload lesson thumbnails
4. Manage course content

### For Administrators
1. Access admin panel at `/admin`
2. Manage users and their roles
3. Oversee course and lesson creation
4. View system statistics and analytics

## Project Structure

```
raven_project/
├── app.py                 # Application factory and configuration
├── run.py                 # Application entry point
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── .gitignore            # Git ignore rules
│
├── admin/                # Admin module
│   ├── __init__.py
│   ├── routes.py         # Admin routes and logic
│   └── forms.py          # Admin forms
│
├── courses/              # Course management
│   ├── __init__.py
│   ├── routes.py         # Course routes
│   └── forms.py          # Course forms
│
├── lessons/              # Lesson management
│   ├── __init__.py
│   ├── routes.py         # Lesson routes
│   └── forms.py          # Lesson forms
│
├── users/                # User management
│   ├── __init__.py
│   ├── routes.py         # User routes
│   └── forms.py          # User forms
│
├── main/                 # Main application
│   ├── __init__.py
│   └── routes.py         # Main routes
│
├── raven/                # Static files and templates
│   ├── static/           # CSS, JS, images
│   │   ├── css/          # Stylesheets
│   │   ├── img/          # Images
│   │   ├── user_pics/    # User profile pictures
│   │   ├── course_icons/ # Course icons
│   │   └── lesson_thumbnails/ # Lesson thumbnails
│   └── templates/        # HTML templates
│       ├── admin/        # Admin templates
│       └── *.html        # Main templates
│
├── migrations/           # Database migrations
│   ├── versions/         # Migration files
│   └── alembic.ini       # Alembic configuration
│
└── instance/             # Instance-specific files
    └── site.db          # SQLite database (development)
```

## API Documentation

### Authentication Endpoints
- `POST /users/register` - User registration
- `POST /users/login` - User login
- `POST /users/logout` - User logout
- `POST /users/reset_password` - Request password reset
- `GET /users/reset_token/<token>` - Reset password with token

### Course Endpoints
- `GET /courses/allcourses` - List all courses
- `GET /courses/course/<course_title>` - View specific course
- `POST /courses/new_course` - Create new course (authenticated)
- `GET /courses/new_course` - Course creation form

### Lesson Endpoints
- `GET /lessons/lesson/<lesson_slug>` - View specific lesson
- `POST /lessons/new_lesson` - Create new lesson (authenticated)
- `GET /lessons/new_lesson` - Lesson creation form
- `POST /lessons/<lesson_slug>/edit` - Edit lesson (author only)

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/courses` - Course management
- `GET /admin/lessons` - Lesson management
- `GET /admin/stats` - System statistics

## Security Features

### Authentication & Authorization
- Secure password hashing with bcrypt
- Session-based authentication
- Role-based access control
- CSRF protection on all forms

### Data Protection
- SQL injection prevention through ORM
- HTML sanitization for user content
- Secure file upload handling
- Rate limiting on sensitive operations

### Email Security
- Token-based password reset
- Email verification system
- Rate limiting on email requests
- Secure token generation and validation

## Development

### Adding New Features
1. Create a new blueprint in a separate directory
2. Add forms in `forms.py`
3. Add routes in `routes.py`
4. Register the blueprint in `app.py`
5. Create corresponding templates

### Database Changes
1. Modify models in `models.py`
2. Create migration: `flask db migrate -m "Description"`
3. Apply migration: `flask db upgrade`

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Maintain consistent naming conventions

## Deployment

### Production Checklist
- [ ] Set strong `SECRET_KEY` in environment
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Configure proper email settings
- [ ] Enable HTTPS
- [ ] Set up proper logging
- [ ] Configure static file serving
- [ ] Set up backup strategy
- [ ] Configure monitoring

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide in SETUP.md

## Acknowledgments

- Flask community for the excellent framework
- Bootstrap team for the CSS framework
- CKEditor team for the rich text editor
- All contributors and testers

---

**Note**: This project is designed for educational purposes. Ensure proper security measures are in place before deploying to production.