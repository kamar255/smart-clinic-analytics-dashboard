import os
import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine, text

# 🌟 Solve encoding issues (UnicodeDecodeError) for Windows environments
os.environ['PGCLIENTENCODING'] = 'utf-8'
# Initialize Faker and set random seeds to ensure data reproducibility
fake = Faker()
Faker.seed(42)  
random.seed(42)

DATABASE_URL = "postgresql://postgres:1234@localhost:5432/SmartClinicDB"
engine = create_engine(DATABASE_URL)

print("Generating smart mock data and inserting into PostgreSQL database...")
try:

    specialties = ["Cardiology", "Pediatrics", "Orthopedics", "Dermatology", "Neurology"]
    doctors_data = []
    for i in range(1, 11):  
        doctors_data.append({
            "name": f"Dr. {fake.name()}",
            "specialty": random.choice(specialties),
            "avg_consultation_time": random.choice([15, 20, 30])
        })
    pd.DataFrame(doctors_data).to_sql('doctors', engine, if_exists='append', index=False)

    
    patients_data = []
    for i in range(1, 201):  
        patients_data.append({
            "name": fake.name(),
            "gender": random.choice(["Male", "Female"]),
            "age": random.randint(1, 85),
            "commitment_score": 100  
        })
    pd.DataFrame(patients_data).to_sql('patients', engine, if_exists='append', index=False)

    # GENERATE APPOINTMENTS AND BILLING DATA
    patient_ids = list(range(1, 201))
    doctor_ids = list(range(1, 11))
    appointments_data = []
    billing_data = []
    start_date = datetime.now().date() - timedelta(days=30)  

    for app_id in range(1, 1001):
        p_id = random.choice(patient_ids)
        d_id = random.choice(doctor_ids)
        app_date = fake.date_between(start_date=start_date, end_date="today")
        base_time = datetime.strptime(f"{random.randint(9, 16)}:{random.choice([0, 15, 30, 45])}", "%H:%M")
        scheduled_time = base_time.time()
        arrival_status = random.choices(["Attended", "No-Show", "Cancelled"], weights=[80, 12, 8], k=1)[0]
        urgency_level = random.choices(["Routine", "Urgent", "Emergency"], weights=[85, 10, 5], k=1)[0]
        
        actual_start_time = None
        delay_minutes = 0
        amount_charged = 50.00  
        no_show_penalty = 0.00
        
        if arrival_status == "Attended":
            if urgency_level == "Emergency":
                delay_minutes = random.randint(20, 45)
            elif urgency_level == "Urgent":
                delay_minutes = random.randint(10, 25)
            else:
                delay_minutes = random.randint(-5, 15)
            
            actual_datetime = datetime.combine(app_date, scheduled_time) + timedelta(minutes=max(0, delay_minutes))
            actual_start_time = actual_datetime.time()
        elif arrival_status == "No-Show":
            no_show_penalty = 20.00
            
        appointments_data.append({
            "patient_id": p_id,
            "doctor_id": d_id,
            "appointment_date": app_date,
            "scheduled_time": scheduled_time,
            "actual_start_time": actual_start_time,
            "arrival_status": arrival_status,
            "urgency_level": urgency_level,
            "delay_minutes": max(0, delay_minutes)
        })
        billing_data.append({
            "appointment_id": app_id,
            "amount_charged": amount_charged,
            "no_show_penalty": no_show_penalty
        })

    pd.DataFrame(appointments_data).to_sql('appointments', engine, if_exists='append', index=False)
    pd.DataFrame(billing_data).to_sql('billing', engine, if_exists='append', index=False)
#--- D) UPDATE PATIENT COMMITMENT SCORES ---
    with engine.begin() as connection:
        connection.execute(text("""
            UPDATE Patients p
            SET commitment_score = GREATEST(0, 100 - (
                SELECT COUNT(*) * 15 
                FROM Appointments a 
                WHERE a.patient_id = p.patient_id AND a.arrival_status = 'No-Show'
            ));
        """))

    print("Data generation and insertion completed successfully!")

except Exception as e:
    print(f"An error occurred while generating data: {e}")