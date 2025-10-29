import os
import json
import firebase_admin
from firebase_admin import credentials, db, messaging
from datetime import datetime, timedelta

firebase_json = os.environ.get("FIREBASE_KEY")
if not firebase_json:
    raise Exception("FIREBASE_KEY not found in environment variables")

cred_dict = json.loads(firebase_json)

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://mybabyvax-3d5cc-default-rtdb.firebaseio.com/"
})

def send_fcm(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    response = messaging.send(message)
    print("Sent notification:", response)

def check_schedules():
    today = datetime.now().date()
    users_ref = db.reference("users")
    users = users_ref.get()

    if not users:
        print("No users found.")
        return

    for uid, user in users.items():
        babies = user.get("babies", {})
        for baby_id, baby in babies.items():
            schedules = baby.get("schedules", {})
            for vaccine_name, vaccine in schedules.items():
                doses = vaccine.get("doses", [])
                for dose in doses:
                    dose_date_str = dose.get("date")
                    if not dose_date_str:
                        continue
                    dose_date = datetime.strptime(dose_date_str, "%Y-%m-%d").date()
                    days_left = (dose_date - today).days

                    print(f"User: {uid}, Baby: {baby.get('fullName')}, Dose: {dose.get('doseName')}, Date: {dose_date_str}, Days left: {days_left}")

                    if days_left == 3:
                        title = f"Upcoming Vaccine for {baby.get('fullName')}"
                        body = f"{dose.get('doseName')} of {vaccine.get('vaccineName')} is scheduled in 3 days on {dose_date_str}"
                    elif days_left == 1:
                        title = f"Vaccine Scheduled Today for {baby.get('fullName')}"
                        body = f"{dose.get('doseName')} of {vaccine.get('vaccineName')} is scheduled today ({dose_date_str})"
                    else:
                        continue

                    fcm_token = user.get("fcmToken")
                    if fcm_token:
                        send_fcm(fcm_token, title, body)
                    else:
                        print(f"No FCM token for user {uid}, would send: {title} - {body}")

if __name__ == "__main__":
    check_schedules()
