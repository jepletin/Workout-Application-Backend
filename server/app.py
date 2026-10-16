from datetime import date

from flask import Flask, make_response, request
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from models import *

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)



# 1. GET: Retrieve all workouts
@app.route('/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.all()

    workout_list = []

    for workout in workouts:
        workout_data = {
            'id': workout.id,
            'date': workout.date.isoformat(),
            'duration_minutes': workout.duration_minutes,
            'notes': workout.notes
        }

        workout_list.append(workout_data)

    return make_response(workout_list, 200)


# 2. GET: Retrieve one workout by ID,
# including its exercises and workout details
@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout_by_id(id):
    workout = db.session.get(Workout, id)

    if workout is None:
        return make_response(
            {'error': 'Workout not found'},
            404
        )

    workout_exercises = []

    for item in workout.workout_exercises:
        exercise_data = {
            'id': item.exercise.id,
            'name': item.exercise.name,
            'category': item.exercise.category,
            'equipment_needed': item.exercise.equipment_needed,
            'reps': item.reps,
            'sets': item.sets,
            'duration_seconds': item.duration_seconds
        }

        workout_exercises.append(exercise_data)

    workout_data = {
        'id': workout.id,
        'date': workout.date.isoformat(),
        'duration_minutes': workout.duration_minutes,
        'notes': workout.notes,
        'workout_exercises': workout_exercises
    }

    return make_response(workout_data, 200)


# 3. POST: Create a new workout
@app.route('/workouts', methods=['POST'])
def create_workout():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response(
            {'error': 'Request body must contain valid JSON'},
            400
        )

    try:
        workout_date = date.fromisoformat(data['date'])
        duration = data['duration_minutes']

        if isinstance(duration, bool):
            raise ValueError

        if not isinstance(duration, int):
            raise ValueError

        if duration <= 0:
            return make_response(
                {'error': 'duration_minutes must be greater than zero'},
                400
            )

    except (KeyError, ValueError, TypeError):
        return make_response(
            {
                'error': (
                    'Provide a valid date in YYYY-MM-DD format '
                    'and a positive integer duration_minutes'
                )
            },
            400
        )

    workout = Workout(
        date=workout_date,
        duration_minutes=duration,
        notes=data.get('notes')
    )

    db.session.add(workout)
    db.session.commit()

    workout_data = {
        'id': workout.id,
        'date': workout.date.isoformat(),
        'duration_minutes': workout.duration_minutes,
        'notes': workout.notes
    }

    return make_response(workout_data, 201)


# 4. DELETE: Delete a workout and its associated
# workout-exercise records
@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)

    if workout is None:
        return make_response(
            {'error': 'Workout not found'},
            404
        )

    db.session.delete(workout)
    db.session.commit()

    return make_response(
        {'message': 'Workout deleted successfully'},
        200
    )



# 5. GET: Retrieve all exercises
@app.route('/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.all()

    exercise_list = []

    for exercise in exercises:
        exercise_data = {
            'id': exercise.id,
            'name': exercise.name,
            'category': exercise.category,
            'equipment_needed': exercise.equipment_needed
        }

        exercise_list.append(exercise_data)

    return make_response(exercise_list, 200)


# 6. GET: Retrieve one exercise by ID,
# including its associated workouts
@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise_by_id(id):
    exercise = db.session.get(Exercise, id)

    if exercise is None:
        return make_response(
            {'error': 'Exercise not found'},
            404
        )

    workouts = []

    for item in exercise.workout_exercises:
        workout_data = {
            'id': item.workout.id,
            'date': item.workout.date.isoformat(),
            'duration_minutes': item.workout.duration_minutes,
            'notes': item.workout.notes,
            'reps': item.reps,
            'sets': item.sets,
            'duration_seconds': item.duration_seconds
        }

        workouts.append(workout_data)

    exercise_data = {
        'id': exercise.id,
        'name': exercise.name,
        'category': exercise.category,
        'equipment_needed': exercise.equipment_needed,
        'workouts': workouts
    }

    return make_response(exercise_data, 200)


# 7. POST: Create a new exercise
@app.route('/exercises', methods=['POST'])
def create_exercise():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response(
            {'error': 'Request body must contain valid JSON'},
            400
        )

    name = data.get('name')
    category = data.get('category')
    equipment_needed = data.get('equipment_needed', False)

    if not isinstance(name, str) or not name.strip():
        return make_response(
            {'error': 'A valid exercise name is required'},
            400
        )

    if not isinstance(category, str) or not category.strip():
        return make_response(
            {'error': 'A valid exercise category is required'},
            400
        )

    if not isinstance(equipment_needed, bool):
        return make_response(
            {'error': 'equipment_needed must be true or false'},
            400
        )

    exercise = Exercise(
        name=name,
        category=category,
        equipment_needed=equipment_needed
    )

    db.session.add(exercise)
    db.session.commit()

    exercise_data = {
        'id': exercise.id,
        'name': exercise.name,
        'category': exercise.category,
        'equipment_needed': exercise.equipment_needed
    }

    return make_response(exercise_data, 201)


# 8. DELETE: Delete an exercise and its associated
# workout-exercise records
@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)

    if exercise is None:
        return make_response(
            {'error': 'Exercise not found'},
            404
        )

    db.session.delete(exercise)
    db.session.commit()

    return make_response(
        {'message': 'Exercise deleted successfully'},
        200
    )



# 9. POST: Associate an exercise with a workout
@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST']
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    exercise = db.session.get(Exercise, exercise_id)

    if workout is None:
        return make_response(
            {'error': 'Workout not found'},
            404
        )

    if exercise is None:
        return make_response(
            {'error': 'Exercise not found'},
            404
        )

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return make_response(
            {'error': 'Request body must contain valid JSON'},
            400
        )
    existing = WorkoutExercise.query.filter_by(
        workout_id=workout_id,
        exercise_id=exercise_id
    ).first()

    if existing is not None:
        return make_response(
            {'error': 'This exercise is already in this workout'},
            409
        )
    reps = data.get('reps')
    sets = data.get('sets')
    duration_seconds = data.get('duration_seconds')
    values = {
        'reps': reps,
        'sets': sets,
        'duration_seconds': duration_seconds
    }

    for field, value in values.items():
        if value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                return make_response(
                    {'error': f'{field} must be a positive integer'},
                    400
                )

    workout_exercise = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        reps=reps,
        sets=sets,
        duration_seconds=duration_seconds
    )

    db.session.add(workout_exercise)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

        return make_response(
            {'error': 'Could not associate this exercise with the workout'},
            409
        )

    response_data = {
        'id': workout_exercise.id,
        'workout_id': workout_exercise.workout_id,
        'exercise_id': workout_exercise.exercise_id,
        'reps': workout_exercise.reps,
        'sets': workout_exercise.sets,
        'duration_seconds': workout_exercise.duration_seconds
    }

    return make_response(response_data, 201)
if __name__ == '__main__':
    app.run(port=5555, debug=True)