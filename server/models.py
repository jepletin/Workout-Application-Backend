from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy import CheckConstraint, UniqueConstraint

db = SQLAlchemy()

# Define Models here


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # Relationships
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='exercise',
        cascade='all, delete-orphan'
    )

    workouts = db.relationship(
        'Workout',
        secondary='workout_exercises',
        back_populates='exercises',
        viewonly=True
    )

    # Model validations
    @validates('name')
    def validate_name(self, key, value):
        if not value or not value.strip():
            raise ValueError('Exercise name cannot be empty.')

        return value.strip()

    @validates('category')
    def validate_category(self, key, value):
        if not value or not value.strip():
            raise ValueError('Exercise category cannot be empty.')

        return value.strip()


class Workout(db.Model):
    __tablename__ = 'workouts'

    # Database constraint
    __table_args__ = (
        CheckConstraint(
            'duration_minutes > 0',
            name='check_workout_duration_positive'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    # Relationships
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='workout',
        cascade='all, delete-orphan'
    )

    exercises = db.relationship(
        'Exercise',
        secondary='workout_exercises',
        back_populates='workouts',
        viewonly=True
    )

    # Model validation
    @validates('duration_minutes')
    def validate_duration_minutes(self, key, value):
        if value is None or value <= 0:
            raise ValueError(
                'Workout duration must be greater than zero.'
            )

        return value


class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'

    # Database constraints
    __table_args__ = (
        UniqueConstraint(
            'workout_id',
            'exercise_id',
            name='unique_exercise_per_workout'
        ),
        CheckConstraint(
            'reps IS NULL OR reps > 0',
            name='check_reps_positive'
        ),
        CheckConstraint(
            'sets IS NULL OR sets > 0',
            name='check_sets_positive'
        ),
        CheckConstraint(
            'duration_seconds IS NULL OR duration_seconds > 0',
            name='check_duration_seconds_positive'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    workout_id = db.Column(
        db.Integer,
        db.ForeignKey('workouts.id'),
        nullable=False
    )

    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey('exercises.id'),
        nullable=False
    )

    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    # Relationships
    workout = db.relationship(
        'Workout',
        back_populates='workout_exercises'
    )

    exercise = db.relationship(
        'Exercise',
        back_populates='workout_exercises'
    )

    # Model validation
    @validates('reps', 'sets', 'duration_seconds')
    def validate_positive_values(self, key, value):
        if value is not None and value <= 0:
            raise ValueError(
                f'{key} must be greater than zero.'
            )

        return value