#!/usr/bin/env python3

from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise

with app.app_context():
    # Clear existing data
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()

    # Create exercises
    pushups = Exercise(
        name="Push-ups",
        category="Strength",
        equipment_needed=False
    )

    running = Exercise(
        name="Running",
        category="Cardio",
        equipment_needed=False
    )

    squats = Exercise(
        name="Squats",
        category="Strength",
        equipment_needed=False
    )

    # Save exercises to the database
    db.session.add_all([pushups, running, squats])
    db.session.commit()

    # Create workouts
    workout1 = Workout(
        date=date(2026, 10, 15),
        duration_minutes=30,
        notes="Morning strength workout"
    )

    workout2 = Workout(
        date=date(2026, 10, 16),
        duration_minutes=45,
        notes="Cardio and fitness"
    )

    # Save workouts to the database
    db.session.add_all([workout1, workout2])
    db.session.commit()

    # Connect exercises to workouts
    workout_exercise1 = WorkoutExercise(
        workout_id=workout1.id,
        exercise_id=pushups.id,
        reps=15,
        sets=3,
        duration_seconds=None
    )

    workout_exercise2 = WorkoutExercise(
        workout_id=workout1.id,
        exercise_id=squats.id,
        reps=12,
        sets=3,
        duration_seconds=None
    )

    workout_exercise3 = WorkoutExercise(
        workout_id=workout2.id,
        exercise_id=running.id,
        reps=None,
        sets=None,
        duration_seconds=1800
    )

    db.session.add_all([
        workout_exercise1,
        workout_exercise2,
        workout_exercise3
    ])

    # Save everything
    db.session.commit()

    print("Database seeded successfully!")