from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from models import db, Exercise, Workout, WorkoutExercise


# ---------------------------------------------------------------------------
# Fixtures: setup code that pytest runs for the tests that ask for it
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """A fresh app with an empty in-memory database for every test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers: create data directly in the database
# ---------------------------------------------------------------------------

def add_exercise(app, name='Push-up', category='Strength', equipment_needed=False):
    with app.app_context():
        exercise = Exercise(
            name=name,
            category=category,
            equipment_needed=equipment_needed
        )
        db.session.add(exercise)
        db.session.commit()
        return exercise.id


def add_workout(app, duration_minutes=30, notes='Morning session'):
    with app.app_context():
        workout = Workout(
            date=date(2025, 1, 15),
            duration_minutes=duration_minutes,
            notes=notes
        )
        db.session.add(workout)
        db.session.commit()
        return workout.id


def link(app, workout_id, exercise_id, reps=10, sets=3, duration_seconds=None):
    with app.app_context():
        item = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            reps=reps,
            sets=sets,
            duration_seconds=duration_seconds
        )
        db.session.add(item)
        db.session.commit()
        return item.id


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_exercise_name_is_stripped(self, app):
        with app.app_context():
            exercise = Exercise(name='  Squat  ', category='Legs')
            assert exercise.name == 'Squat'

    def test_exercise_empty_name_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Exercise(name='   ', category='Legs')

    def test_exercise_empty_category_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Exercise(name='Squat', category='')

    def test_workout_zero_duration_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Workout(date=date(2025, 1, 1), duration_minutes=0)

    def test_workout_negative_duration_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Workout(date=date(2025, 1, 1), duration_minutes=-10)

    def test_workout_exercise_negative_reps_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                WorkoutExercise(workout_id=1, exercise_id=1, reps=-5)

    def test_duplicate_exercise_in_workout_not_allowed(self, app):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)
        link(app, workout_id, exercise_id)

        with app.app_context():
            duplicate = WorkoutExercise(
                workout_id=workout_id,
                exercise_id=exercise_id,
                reps=5
            )
            db.session.add(duplicate)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_deleting_workout_deletes_its_links(self, app):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)
        link(app, workout_id, exercise_id)

        with app.app_context():
            workout = db.session.get(Workout, workout_id)
            db.session.delete(workout)
            db.session.commit()

            assert WorkoutExercise.query.count() == 0
            # The exercise itself must still exist
            assert db.session.get(Exercise, exercise_id) is not None


# ---------------------------------------------------------------------------
# Workout route tests
# ---------------------------------------------------------------------------

class TestWorkoutRoutes:
    def test_get_workouts_empty(self, client):
        response = client.get('/workouts')
        assert response.status_code == 200
        assert response.get_json() == []

    def test_get_workouts_returns_all(self, app, client):
        add_workout(app, duration_minutes=30)
        add_workout(app, duration_minutes=45)

        response = client.get('/workouts')
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_get_workout_by_id_includes_exercises(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app, name='Plank', category='Core')
        link(app, workout_id, exercise_id, reps=None, sets=3, duration_seconds=60)

        response = client.get(f'/workouts/{workout_id}')
        data = response.get_json()

        assert response.status_code == 200
        assert data['id'] == workout_id
        assert len(data['workout_exercises']) == 1
        assert data['workout_exercises'][0]['name'] == 'Plank'
        assert data['workout_exercises'][0]['duration_seconds'] == 60

    def test_get_workout_not_found(self, client):
        response = client.get('/workouts/999')
        assert response.status_code == 404
        assert response.get_json()['error'] == 'Workout not found'

    def test_create_workout(self, client):
        response = client.post('/workouts', json={
            'date': '2025-02-01',
            'duration_minutes': 45,
            'notes': 'Leg day'
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data['duration_minutes'] == 45
        assert data['notes'] == 'Leg day'
        assert 'id' in data

    def test_create_workout_without_notes(self, client):
        response = client.post('/workouts', json={
            'date': '2025-02-01',
            'duration_minutes': 20
        })
        assert response.status_code == 201

    def test_create_workout_zero_duration(self, client):
        response = client.post('/workouts', json={
            'date': '2025-02-01',
            'duration_minutes': 0
        })
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_create_workout_missing_fields(self, client):
        response = client.post('/workouts', json={'notes': 'No date or duration'})
        assert response.status_code == 400

    def test_create_workout_invalid_date(self, client):
        response = client.post('/workouts', json={
            'date': 'not-a-date',
            'duration_minutes': 30
        })
        assert response.status_code == 400

    def test_create_workout_no_json_body(self, client):
        response = client.post('/workouts', data='plain text')
        assert response.status_code == 400
        assert response.get_json()['error'] == 'Valid JSON body required'

    def test_delete_workout(self, app, client):
        workout_id = add_workout(app)

        response = client.delete(f'/workouts/{workout_id}')
        assert response.status_code == 200
        assert client.get(f'/workouts/{workout_id}').status_code == 404

    def test_delete_workout_not_found(self, client):
        response = client.delete('/workouts/999')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Exercise route tests
# ---------------------------------------------------------------------------

class TestExerciseRoutes:
    def test_get_exercises_empty(self, client):
        response = client.get('/exercises')
        assert response.status_code == 200
        assert response.get_json() == []

    def test_get_exercises_returns_all(self, app, client):
        add_exercise(app, name='Push-up')
        add_exercise(app, name='Squat', category='Legs')

        response = client.get('/exercises')
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_get_exercise_by_id_includes_workouts(self, app, client):
        workout_id = add_workout(app, notes='Chest day')
        exercise_id = add_exercise(app)
        link(app, workout_id, exercise_id, reps=12, sets=4)

        response = client.get(f'/exercises/{exercise_id}')
        data = response.get_json()

        assert response.status_code == 200
        assert data['name'] == 'Push-up'
        assert len(data['workouts']) == 1
        assert data['workouts'][0]['id'] == workout_id
        assert data['workouts'][0]['date'] == '2025-01-15'
        assert data['workouts'][0]['reps'] == 12

    def test_get_exercise_not_found(self, client):
        response = client.get('/exercises/999')
        assert response.status_code == 404
        assert response.get_json()['error'] == 'Exercise not found'

    def test_create_exercise(self, client):
        response = client.post('/exercises', json={
            'name': 'Deadlift',
            'category': 'Strength',
            'equipment_needed': True
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data['name'] == 'Deadlift'
        assert data['equipment_needed'] is True

    def test_create_exercise_missing_name(self, client):
        response = client.post('/exercises', json={'category': 'Strength'})
        assert response.status_code == 400

    def test_create_exercise_blank_name(self, client):
        response = client.post('/exercises', json={
            'name': '   ',
            'category': 'Strength'
        })
        assert response.status_code == 400

    def test_create_exercise_no_json_body(self, client):
        response = client.post('/exercises', data='plain text')
        assert response.status_code == 400

    def test_delete_exercise(self, app, client):
        exercise_id = add_exercise(app)

        response = client.delete(f'/exercises/{exercise_id}')
        assert response.status_code == 200
        assert client.get(f'/exercises/{exercise_id}').status_code == 404

    def test_delete_exercise_not_found(self, client):
        response = client.delete('/exercises/999')
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Workout <-> Exercise association tests
# ---------------------------------------------------------------------------

class TestWorkoutExerciseRoutes:
    def url(self, workout_id, exercise_id):
        return f'/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises'

    def body(self, workout_id, exercise_id, **extra):
        """Request body. The schema requires both ids, so always include them."""
        return {'workout_id': workout_id, 'exercise_id': exercise_id, **extra}

    def test_add_exercise_to_workout(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)

        response = client.post(
            self.url(workout_id, exercise_id),
            json=self.body(workout_id, exercise_id, reps=10, sets=3)
        )
        data = response.get_json()

        assert response.status_code == 201
        assert data['reps'] == 10
        assert data['sets'] == 3

        # The workout should now list the exercise
        workout = client.get(f'/workouts/{workout_id}').get_json()
        assert len(workout['workout_exercises']) == 1

    def test_add_exercise_with_duration_only(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app, name='Plank', category='Core')

        response = client.post(
            self.url(workout_id, exercise_id),
            json=self.body(workout_id, exercise_id, duration_seconds=90)
        )
        assert response.status_code == 201
        assert response.get_json()['duration_seconds'] == 90

    def test_add_exercise_workout_not_found(self, app, client):
        exercise_id = add_exercise(app)
        response = client.post(
            self.url(999, exercise_id),
            json=self.body(999, exercise_id, reps=5)
        )
        assert response.status_code == 404

    def test_add_exercise_exercise_not_found(self, app, client):
        workout_id = add_workout(app)
        response = client.post(
            self.url(workout_id, 999),
            json=self.body(workout_id, 999, reps=5)
        )
        assert response.status_code == 404

    def test_add_duplicate_exercise_returns_409(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)
        link(app, workout_id, exercise_id)

        response = client.post(
            self.url(workout_id, exercise_id),
            json=self.body(workout_id, exercise_id, reps=5, sets=2)
        )
        assert response.status_code == 409
        assert response.get_json()['error'] == 'Exercise already in this workout'

    def test_add_exercise_zero_reps(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)

        response = client.post(
            self.url(workout_id, exercise_id),
            json=self.body(workout_id, exercise_id, reps=0, sets=3)
        )
        assert response.status_code == 400

    def test_add_exercise_negative_sets(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)

        response = client.post(
            self.url(workout_id, exercise_id),
            json=self.body(workout_id, exercise_id, reps=10, sets=-1)
        )
        assert response.status_code == 400

    def test_add_exercise_missing_ids_in_body(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)

        response = client.post(
            self.url(workout_id, exercise_id),
            json={'reps': 10, 'sets': 3}
        )
        assert response.status_code == 400
        assert 'workout_id' in response.get_json()['error']

    def test_add_exercise_no_json_body(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)

        response = client.post(self.url(workout_id, exercise_id), data='nope')
        assert response.status_code == 400

    def test_deleting_exercise_removes_it_from_workout(self, app, client):
        workout_id = add_workout(app)
        exercise_id = add_exercise(app)
        link(app, workout_id, exercise_id)

        client.delete(f'/exercises/{exercise_id}')

        workout = client.get(f'/workouts/{workout_id}').get_json()
        assert workout['workout_exercises'] == []