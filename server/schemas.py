from marshmallow import fields
from flask_marshmallow import Marshmallow

from app import app
from models import Exercise, Workout, WorkoutExercise


ma = Marshmallow(app)


# Schema for Exercise
class ExerciseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Exercise
        load_instance = False
        include_fk = True


# Schema for Workout
class WorkoutSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Workout
        load_instance = False
        include_fk = True


# Schema for WorkoutExercise
class WorkoutExerciseSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutExercise
        load_instance = False
        include_fk = True