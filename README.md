# Workout Application Backend
# Workout Application Backend

## Project Description

The Workout Application Backend is a RESTful API built with Python and Flask
for managing workouts and exercises.

The API allows users to create, retrieve, and delete workouts and exercises.
It also allows users to associate exercises with workouts while recording
details such as repetitions, sets, and exercise duration.

The application uses Flask-SQLAlchemy to manage database operations,
Flask-Migrate to handle database migrations, SQLite for data storage,
and Marshmallow for serialization, deserialization, and data validation.

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- SQLAlchemy
- Marshmallow
- Flask-Marshmallow
- Marshmallow-SQLAlchemy
- SQLite
- Pipenv

## Project Structure

```text
Workout-Application-Backend/
├── README.md
├── Pipfile
├── Pipfile.lock
└── server/
    ├── app.py
    ├── models.py
    ├── schemas.py
    ├── seed.py
    └── migrations/