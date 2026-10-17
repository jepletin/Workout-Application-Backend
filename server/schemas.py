from marshmallow import validate
from flask_marshmallow import Marshmallow

from app import app
from models import Exercise, Workout, WorkoutExercise

ma = Marshmallow(app)


class ExerciseSchema(ma.SQLAlchemyAutoSchema):
    name = ma.auto_field(
        validate=validate.Length(min=1, error="Exercise name cannot be empty.")
    )

    category = ma.auto_field(
        validate=validate.Length(min=1, error="Exercise category cannot be empty.")
    )

    class Meta:
        model = Exercise
        load_instance = False
        include_fk = True


class WorkoutSchema(ma.SQLAlchemyAutoSchema):
    duration_minutes = ma.auto_field(
        validate=validate.Range(
            min=1,
            error="Workout duration must be greater than zero."
        )
    )

    class Meta:
        model = Workout
        load_instance = False
        include_fk = True


class WorkoutExerciseSchema(ma.SQLAlchemyAutoSchema):
    reps = ma.auto_field(
        validate=validate.Range(
            min=1,
            error="Reps must be greater than zero."
        ),
        allow_none=True
    )

    sets = ma.auto_field(
        validate=validate.Range(
            min=1,
            error="Sets must be greater than zero."
        ),
        allow_none=True
    )

    duration_seconds = ma.auto_field(
        validate=validate.Range(
            min=1,
            error="Duration in seconds must be greater than zero."
        ),
        allow_none=True
    )

    class Meta:
        model = WorkoutExercise
        load_instance = False
        include_fk = True