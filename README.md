# Airport Service API

Airport Service API is a robust backend solution for managing airport operations and tracking flights worldwide. This project models real-world aviation concepts such as airports, routes, flights, airplanes, crews, tickets, and orders, providing a structured and scalable API built with Django Rest Framework.

## Features

- **User Management**: Custom user model using email as the unique identifier.
- **Authentication**: Secure authentication using JWT (JSON Web Tokens).
- **Email Verification & Password Reset**: Support for account activation and password recovery via email.
- **Airport Management**: Manage countries, cities, and airports.
- **Flight Operations**: 
  - Define routes between airports with distance tracking.
  - Manage airplane types and specific airplane fleets (including capacity tracking and images).
  - Schedule flights with automated validation of departure/arrival times.
- **Ordering System**: 
  - Users can place orders for tickets.
  - Ticket validation ensures no overbooking and correct seat/row assignment.
- **API Documentation**: Interactive documentation using Swagger UI and ReDoc.
- **Filtering & Searching**: Advanced filtering for flights (by route, date, etc.).
- **Throttling & Pagination**: Optimized performance with rate limiting and pagination.
- **Docker Support**: Containerized environment for easy deployment and development.

## Technologies Used

- **Framework**: [Django](https://www.djangoproject.com/) & [Django REST Framework](https://www.django-rest-framework.org/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Authentication**: [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- **Documentation**: [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Task Management**: [Python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- **Styling/Linting**: [Black](https://black.readthedocs.io/)

## Installation & Setup

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/airport-api.git
   cd airport-api
   ```

2. **Create a `.env` file**:
   ```bash
   cp .env.sample .env
   ```
   Then populate it with your configuration (see [Environment Variables](#environment-variables)).

3. **Build and run the containers**:
   ```bash
   docker-compose up --build
   ```

4. **The API will be available at**: `http://127.0.0.1:8000/`

### Local Development

1. **Clone the repository and navigate to the project**:
   ```bash
   git clone https://github.com/your-username/airport-api.git
   cd airport-api
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.sample .env
   ```
   Then populate it with your configuration.

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

## Environment Variables

To run this project, you will need to add the following environment variables to your `.env` file (you can use `.env.sample` as a template):

```env
SECRET_KEY=your_django_secret_key

# Database Configuration
POSTGRES_DB=airport_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Email Configuration (for verification and password reset)
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

## API Documentation

The API includes interactive documentation accessible once the server is running:

- **Swagger UI**: [http://127.0.0.1:8000/api/doc/swagger/](http://127.0.0.1:8000/api/doc/swagger/)
- **ReDoc**: [http://127.0.0.1:8000/api/doc/redoc/](http://127.0.0.1:8000/api/doc/redoc/)

## Authentication

This API uses JWT Authentication. To access protected endpoints:

1. **Register** at `/api/user/register/`.
2. **Obtain tokens** at `/api/user/token/`.
3. **Include the token** in the Authorization header of your requests:
   ```http
   Authorization: Bearer <your_access_token>
   ```

## Testing

To run the automated tests, use the following command:

```bash
# Local
python manage.py test

# Docker
docker-compose exec app python manage.py test
```
