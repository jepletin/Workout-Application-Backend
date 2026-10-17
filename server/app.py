from datetime import date

from flask import Flask, make_response, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
import ipdb

from models import *
from schemas import (
    ma,
    ExerciseSchema,
    WorkoutSchema,
    WorkoutExerciseSchema
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.init_app(app)
ma.init_app(app)

# Schema instances
exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_exercise_schema = WorkoutExerciseSchema()


# 1. GET all workouts
@app.route('/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.all()
    return make_response(workouts_schema.dump(workouts), 200)


# 2. GET one workout with its exercises
@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout_by_id(id):
    workout = db.session.get(Workout, id)

    if workout is None:
        return make_response({'error': 'Workout not found'}, 404)

    result = workout_schema.dump(workout)
    result['workout_exercises'] = []

    for item in workout.workout_exercises:
        result['workout_exercises'].append({
            'id': item.exercise.id,
            'name': item.exercise.name,
            'category': item.exercise.category,
            'equipment_needed': item.exercise.equipment_needed,
            'reps': item.reps,
            'sets': item.sets,
            'duration_seconds': item.duration_seconds
        })

    return make_response(result, 200)


# 3. POST a new workout
@app.route('/workouts', methods=['POST'])
def create_workout():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response({'error': 'Valid JSON body required'}, 400)

    try:
        data = workout_schema.load(data)
        data['date'] = date.fromisoformat(data['date'].isoformat()) if isinstance(data['date'], date) else date.fromisoformat(data['date'])

        workout = Workout(**data)
        db.session.add(workout)
        db.session.commit()

        return make_response(workout_schema.dump(workout), 201)

    except (ValidationError, ValueError, TypeError, KeyError) as error:
        db.session.rollback()
        message = error.messages if isinstance(error, ValidationError) else str(error)
        return make_response({'error': message}, 400)


# 4. DELETE a workout
@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)

    if workout is None:
        return make_response({'error': 'Workout not found'}, 404)

    db.session.delete(workout)
    db.session.commit()
    return make_response({'message': 'Workout deleted successfully'}, 200)


# 5. GET all exercises
@app.route('/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.all()
    return make_response(exercises_schema.dump(exercises), 200)


# 6. GET one exercise with associated workouts
@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise_by_id(id):
    exercise = db.session.get(Exercise, id)

    if exercise is None:
        return make_response({'error': 'Exercise not found'}, 404)

    result = exercise_schema.dump(exercise)
    result['workouts'] = []

    for item in exercise.workout_exercises:
        result['workouts'].append({
            'id': item.workout.id,
            'date': item.workout.date.isoformat(),
            'duration_minutes': item.workout.duration_minutes,
            'notes': item.workout.notes,
            'reps': item.reps,
            'sets': item.sets,
            'duration_seconds': item.duration_seconds
        })

    return make_response(result, 200)


# 7. POST a new exercise
@app.route('/exercises', methods=['POST'])
def create_exercise():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response({'error': 'Valid JSON body required'}, 400)

    try:
        data = exercise_schema.load(data)
        exercise = Exercise(**data)

        db.session.add(exercise)
        db.session.commit()

        return make_response(exercise_schema.dump(exercise), 201)

    except (ValidationError, ValueError, TypeError) as error:
        db.session.rollback()
        message = error.messages if isinstance(error, ValidationError) else str(error)
        return make_response({'error': message}, 400)


# 8. DELETE an exercise
@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)

    if exercise is None:
        return make_response({'error': 'Exercise not found'}, 404)

    db.session.delete(exercise)
    db.session.commit()
    return make_response({'message': 'Exercise deleted successfully'}, 200)


# 9. Associate an exercise with a workout
@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST']
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    exercise = db.session.get(Exercise, exercise_id)

    if workout is None or exercise is None:
        return make_response({'error': 'Workout or exercise not found'}, 404)

    if WorkoutExercise.query.filter_by(
        workout_id=workout_id, exercise_id=exercise_id
    ).first():
        return make_response({'error': 'Exercise already in this workout'}, 409)

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response({'error': 'Valid JSON body required'}, 400)

    try:
        data = workout_exercise_schema.load(data)
        data.pop('workout_id', None)
        data.pop('exercise_id', None)

        item = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            **data
        )

        db.session.add(item)
        db.session.commit()

        return make_response(workout_exercise_schema.dump(item), 201)

    except (ValidationError, ValueError, TypeError) as error:
        db.session.rollback()
        message = error.messages if isinstance(error, ValidationError) else str(error)
        return make_response({'error': message}, 400)

    except IntegrityError:
        db.session.rollback()
        return make_response({'error': 'Could not add exercise to workout'}, 409)


if __name__ == '__main__':
    app.run(port=5555, debug=True)