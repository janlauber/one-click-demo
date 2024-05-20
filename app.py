import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, joinedload, relationship, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, poolclass=NullPool)  # Use NullPool for Kubernetes
Session = sessionmaker(bind=engine)

session = Session()

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    exercise = relationship("Exercise", lazy="joined")


# Create the tables if they don't exist
Base.metadata.create_all(engine)


# Function to insert a workout log
def insert_workout_log(date, exercise_id, sets, reps, weight):
    session = Session()
    new_log = WorkoutLog(
        date=date, exercise_id=exercise_id, sets=sets, reps=reps, weight=weight
    )
    session.add(new_log)
    session.commit()
    session.close()


# Function to update a workout log
def update_workout_log(log_id, date, exercise_id, sets, reps, weight):
    session = Session()
    log = session.query(WorkoutLog).filter_by(id=log_id).one()
    log.date = date
    log.exercise_id = exercise_id
    log.sets = sets
    log.reps = reps
    log.weight = weight
    session.commit()
    session.close()


# Function to delete a workout log
def delete_workout_log(log_id):
    session = Session()
    log = session.query(WorkoutLog).filter_by(id=log_id).one()
    session.delete(log)
    session.commit()
    session.close()


# Function to retrieve all workout logs
def get_workout_logs():
    session = Session()
    logs = session.query(WorkoutLog).options(joinedload(WorkoutLog.exercise)).all()
    session.close()
    return logs


# Function to get all exercises
def get_exercises():
    session = Session()
    exercises = session.query(Exercise).all()
    session.close()
    return exercises


# Function to insert a new exercise
def insert_exercise(name):
    session = Session()
    new_exercise = Exercise(name=name)
    session.add(new_exercise)
    session.commit()
    session.close()


# Function to get the last log for a specific exercise
def get_last_log(exercise_id):
    session = Session()
    log = (
        session.query(WorkoutLog)
        .filter_by(exercise_id=exercise_id)
        .order_by(WorkoutLog.date.desc())
        .first()
    )
    session.close()
    return log


# Function to get the workout logs for an exercise
def get_exercise_logs(exercise_id):
    session = Session()
    logs = (
        session.query(WorkoutLog)
        .filter_by(exercise_id=exercise_id)
        .order_by(WorkoutLog.date)
        .all()
    )
    session.close()
    return logs


# Function to calculate the recommended weight
def calculate_recommendation(logs, base_increase=2.5, max_increase=5.0, min_sessions=3):
    if len(logs) < min_sessions:
        return None

    recent_logs = logs[-min_sessions:]
    success = all(
        log.reps >= 8 for log in recent_logs
    )  # Assuming target is 3 sets of 8 reps

    if success:
        last_weight = logs[-1].weight
        increase = min(last_weight * (base_increase / 100), max_increase)
        return last_weight + increase
    else:
        return logs[-1].weight


# Streamlit App
st.set_page_config(page_title="Fitness Tracker", page_icon="🏋️", layout="wide")

# Custom CSS for mobile-friendly UI
st.markdown(
    """
    <style>
        @media (max-width: 600px) {
            .block-container {
                padding: 1rem 1rem 1rem 1rem;
            }
            .stButton button {
                width: 100%;
            }
            .stTextInput, .stNumberInput {
                width: 100% !important;
            }
            .stDateInput {
                width: 100%;
            }
        }
        .css-1aumxhk {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .stTextInput > div > input {
            border-radius: 10px;
        }
        .stNumberInput > div > input {
            border-radius: 10px;
        }
        .stDateInput > div > input {
            border-radius: 10px;
        }
        .stButton > button {
            border-radius: 10px;
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏋️ Fitness Tracker")

# Add new exercises
st.header("Add New Exercise")
with st.form(key="exercise_form"):
    exercise_name = st.text_input("Exercise Name", key="exercise_name")
    submit_exercise = st.form_submit_button(label="Add Exercise")

if submit_exercise:
    if exercise_name:
        insert_exercise(exercise_name)
        st.success("Exercise added successfully!")
    else:
        st.error("Please provide an exercise name.")

# Log workouts
st.header("Log Your Workout")
exercises = get_exercises()
exercise_options = {exercise.id: exercise.name for exercise in exercises}
if exercise_options:
    selected_exercise_id = st.selectbox(
        "Exercise",
        options=list(exercise_options.keys()),
        format_func=lambda x: exercise_options[x],
    )

    if selected_exercise_id:
        last_log = get_last_log(selected_exercise_id)
        if last_log:
            last_sets = last_log.sets
            last_reps = last_log.reps
            last_weight = last_log.weight
        else:
            last_sets = 3
            last_reps = 8
            last_weight = 20.0

        with st.form(key="workout_form"):
            workout_date = st.date_input("Date", value=date.today())
            sets = st.number_input(
                "Sets", min_value=1, max_value=10, step=1, value=last_sets
            )
            reps = st.number_input(
                "Reps", min_value=1, max_value=100, step=1, value=last_reps
            )
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=500.0,
                step=0.5,
                value=last_weight,
            )
            submit_workout = st.form_submit_button(label="Log Workout")

        if submit_workout:
            if sets and reps and weight:
                insert_workout_log(
                    workout_date, selected_exercise_id, sets, reps, weight
                )
                st.success("Workout logged successfully!")
            else:
                st.error("Please fill in all fields.")

# Edit or delete workout logs
st.header("Edit or Delete Workout Logs")
logs = get_workout_logs()

if logs:
    df = pd.DataFrame(
        [
            {
                "Log ID": log.id,
                "Date": log.date,
                "Exercise": log.exercise.name,
                "Sets": log.sets,
                "Reps": log.reps,
                "Weight (kg)": log.weight,
            }
            for log in logs
        ]
    )
    st.dataframe(df)

    log_id_to_edit = st.number_input(
        "Enter Log ID to Edit or Delete", min_value=1, step=1
    )
    selected_log = None

    try:
        selected_log = session.query(WorkoutLog).filter_by(id=log_id_to_edit).one()
    except NoResultFound:
        st.warning("Log ID not found")

    if selected_log:
        with st.form(key="edit_workout_form"):
            workout_date = st.date_input("Date", value=selected_log.date)
            selected_exercise_id = st.selectbox(
                "Exercise",
                options=list(exercise_options.keys()),
                index=list(exercise_options.keys()).index(selected_log.exercise_id),
                format_func=lambda x: exercise_options[x],
            )
            sets = st.number_input(
                "Sets", min_value=1, max_value=10, step=1, value=selected_log.sets
            )
            reps = st.number_input(
                "Reps", min_value=1, max_value=100, step=1, value=selected_log.reps
            )
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=500.0,
                step=0.5,
                value=selected_log.weight,
            )
            submit_edit = st.form_submit_button(label="Edit Workout")
            submit_delete = st.form_submit_button(label="Delete Workout")

        if submit_edit:
            if sets and reps and weight:
                update_workout_log(
                    log_id_to_edit,
                    workout_date,
                    selected_exercise_id,
                    sets,
                    reps,
                    weight,
                )
                st.success("Workout updated successfully!")
            else:
                st.error("Please fill in all fields.")

        if submit_delete:
            delete_workout_log(log_id_to_edit)
            st.success("Workout deleted successfully!")

# Visualization
st.header("Progress Over Time")
exercise_names = list(exercise_options.values())
selected_exercise_name = st.selectbox(
    "Select Exercise for Progress Visualization", exercise_names
)

if selected_exercise_name:
    selected_exercise_id = [
        key
        for key, value in exercise_options.items()
        if value == selected_exercise_name
    ][0]
    exercise_logs = [log for log in logs if log.exercise_id == selected_exercise_id]

    if exercise_logs:
        df_exercise = pd.DataFrame(
            [{"Date": log.date, "Weight (kg)": log.weight} for log in exercise_logs]
        )
        df_exercise["Date"] = pd.to_datetime(df_exercise["Date"])
        df_exercise = df_exercise.sort_values(by="Date")

        fig = px.line(
            df_exercise,
            x="Date",
            y="Weight (kg)",
            title=f"Weight Progression for {selected_exercise_name}",
            markers=True,
            template="plotly_white",
        )
        fig.update_layout(
            autosize=True,
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write(f"No logs found for {selected_exercise_name}.")

# Recommendation system for linear progression
st.header("Exercise Recommendations")
st.markdown(
    """
    <div style="background-color:#f9f9f9;padding:1rem;border-radius:10px;">
        <h4>How Recommendations Work</h4>
        <p>We recommend increasing the weight based on your recent performance. If you have successfully completed your target reps (e.g., 3 sets of 8 reps) in your last few sessions, we'll suggest a weight increase. Otherwise, we recommend maintaining the current weight.</p>
    </div>
""",
    unsafe_allow_html=True,
)

base_increase = st.slider(
    "Base Increase (%)",
    min_value=1.0,
    max_value=5.0,
    value=2.5,
    step=0.1,
    help="The base percentage increase applied if progression criteria are met.",
)
max_increase = st.slider(
    "Max Increase (kg)",
    min_value=0.5,
    max_value=10.0,
    value=2.5,
    step=0.1,
    help="The maximum weight increase in kilograms.",
)
min_sessions = st.slider(
    "Minimum Sessions for Progression",
    min_value=1,
    max_value=10,
    value=3,
    step=1,
    help="The minimum number of sessions needed to evaluate progression.",
)

for exercise_id, exercise_name in exercise_options.items():
    exercise_logs = get_exercise_logs(exercise_id)
    recommendation = calculate_recommendation(
        exercise_logs, base_increase, max_increase, min_sessions
    )
    if recommendation is not None:
        st.markdown(
            f"""
            <div style="background-color:#e0f7fa;padding:0.5rem;margin:0.5rem 0;border-radius:10px;">
                <h4>{exercise_name}</h4>
                <p>Last logged weight: {exercise_logs[-1].weight:.2f} kg</p>
                <p><strong>Recommended weight:</strong> {recommendation:.2f} kg</p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color:#ffebee;padding:0.5rem;margin:0.5rem 0;border-radius:10px;">
                <h4>{exercise_name}</h4>
                <p>Not enough data to make a recommendation. Keep logging your workouts!</p>
            </div>
        """,
            unsafe_allow_html=True,
        )
