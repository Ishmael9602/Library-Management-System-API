# Library Management System API

A comprehensive REST API for managing library operations built with Django REST Framework.

## Features

- User authentication and registration
- Book catalog management
- Checkout/return functionality
- Inventory tracking
- Search and filtering
- Admin statistics
- Token-based authentication

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### Books
- `GET /api/books/` - List all books
- `POST /api/books/` - Create book (Admin)
- `GET /api/books/{id}/` - Book details
- `GET /api/books/available/` - Available books
- `GET /api/books/search/` - Search books
- `POST /api/books/{id}/checkout/` - Checkout book
- `POST /api/books/{id}/return_book/` - Return book

### Checkouts
- `GET /api/checkouts/my/` - Current user's checkouts
- `GET /api/checkouts/history/` - Checkout history

### Statistics (Admin)
- `GET /api/stats/` - Library statistics

## Setup

1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv/Scripts/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Start server: `python manage.py runserver`

## Technology Stack

- Django 5.2.4
- Django REST Framework
- SQLite/MySQL
- Token Authentication
- Python 3.13
