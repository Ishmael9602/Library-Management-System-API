# Library Management System API

A comprehensive REST API for managing all library operations, including user management, book cataloging, and checkout/return workflows. This API is designed to demonstrate real-world backend development using Django REST Framework with token-based authentication and role-based permissions.

---

## Overview

The **Library Management System API** provides:

* **User Management**: Registration, login, logout, and profile updates
* **Book Management**: View, search, filter, and manage book inventory
* **Checkout & Return**: Borrow and return books with automatic availability tracking
* **Statistics**: Admin-only insights into library usage and popular books
* **Health Monitoring**: Quick API health checks to ensure availability

**Intended Users:**

* **Regular users**: Can view books, checkout, and return them
* **Admins**: Can manage book inventory, view statistics, and monitor usage

---

## Technology Stack

* **Backend Framework**: Django 5.x
* **API Framework**: Django REST Framework (DRF)
* **Authentication**: Token-based authentication via `rest_framework.authtoken`
* **Database**: SQLite (development), PostgreSQL/MySQL (production-ready)
* **Filtering & Searching**: DjangoFilterBackend and DRF Search/Ordering filters
* **Pagination**: StandardResultsSetPagination for paginated results
* **Libraries Used**:

  * `django-filter` → For filtering books
  * `djangorestframework` → For building REST APIs
  * `rest_framework.authtoken` → For secure token-based auth
* **Deployment**: Compatible with Heroku, DigitalOcean, PythonAnywhere

---

## How It Works

1. **Authentication**: Users register and login to receive a token.
2. **Token Usage**: All protected endpoints require the token in the `Authorization` header.

   ```
   Authorization: Token <your_token>
   ```
3. **Role-Based Access**:

   * Only admins can create/update books and view library statistics.
   * Regular users can view books, checkout, and return books.

---

## Demo Setup

```bash
# Clone repository
git clone <repository-url>
cd Library-Management-System-API

# Setup virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

Server runs at: `http://localhost:8000`

---

## API Endpoints Overview

Below is a **full demo of the endpoints** with explanations, request bodies, and expected responses. These can be used for testing or live demonstrations.

---

### **Authentication & User Management**

1. **Register User**
   **POST** `/api/auth/register/`
   **Purpose**: Create a new user account
   **Request Body**:

   ```json
   {
     "username": "libraryuser",
     "email": "user@library.com",
     "password": "securepass123",
     "password_confirm": "securepass123",
     "first_name": "John",
     "last_name": "Doe"
   }
   ```

   **Response**:

   ```json
   {
     "message": "User registered successfully",
     "user": {"id": 1, "username": "libraryuser", "email": "user@library.com"},
     "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
   }
   ```

2. **Login User**
   **POST** `/api/auth/login/`
   **Purpose**: Authenticate user and retrieve token
   **Request Body**:

   ```json
   {"username": "libraryuser", "password": "securepass123"}
   ```

   **Response**:

   ```json
   {
     "message": "Login successful",
     "user": {"id": 1, "username": "libraryuser", "email": "user@library.com"},
     "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
   }
   ```

3. **Logout User**
   **POST** `/api/auth/logout/`
   **Headers:** `Authorization: Token <your_token>`
   **Response**:

   ```json
   {"message": "Logout successful"}
   ```

4. **User Profile**
   **GET / PUT** `/api/auth/profile/`
   **Headers:** `Authorization: Token <your_token>`
   **Purpose**: View or update profile information

---

### **Book Management**

1. **View Available Books**
   **GET** `/api/books/available/`
   **Purpose**: List all books with copies available
   **Response**:

   ```json
   {
     "count": 1,
     "results": [{"book_id": "...", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"}]
   }
   ```

2. **Checkout Book**
   **POST** `/api/books/<book_id>/checkout/`
   **Headers:** `Authorization: Token <your_token>`
   **Purpose**: Borrow a book
   **Request Body (optional)**:

   ```json
   {"notes": "Looking forward to reading this classic!"}
   ```

   **Response**:

   ```json
   {"message": "Book checked out", "checkout": {"checkout_id": "...", "book_title": "The Great Gatsby"}}
   ```

3. **Return Book**
   **POST** `/api/books/<book_id>/return_book/`
   **Headers:** `Authorization: Token <your_token>`
   **Purpose**: Return a borrowed book
   **Response**:

   ```json
   {"message": "Book returned", "checkout": {"checkout_id": "...", "is_returned": true}}
   ```

4. **Search Books**
   **GET** `/api/books/search/?search=<title_or_author>`
   **Purpose**: Filter books by title, author, or availability

---

### **Checkout Management**

1. **View My Current Checkouts**
   **GET** `/api/checkouts/my/`
   **Headers:** `Authorization: Token <your_token>`

2. **Checkout History**
   **GET** `/api/checkouts/history/`
   **Headers:** `Authorization: Token <your_token>`

3. **Overdue Checkouts**
   **GET** `/api/checkouts/overdue/`
   **Headers:** `Authorization: Token <your_token>`

---

### **Admin Endpoints**

1. **Library Statistics**
   **GET** `/api/stats/`
   **Headers:** `Authorization: Token <admin_token>`
   **Purpose**: Monitor book inventory, checkouts, active users, and overdue books

---

### **Utility**

1. **Health Check**
   **GET** `/api/health/`
   **Purpose**: Confirm the API is running

2. **API Index**
   **GET** `/api/index/`
   **Purpose**: Welcome endpoint for API verification

---

### Key Features

* Token-based authentication & authorization
* Role-based access control (Admin vs User)
* Real-time inventory and availability tracking
* Complete checkout/return workflow
* Filtering, searching, and pagination support
