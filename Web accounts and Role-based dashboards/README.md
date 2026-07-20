# Automated Attendance — Step 2

This step adds the web/account layer while keeping the code separated and object-oriented.

## Features

- Student registration with name and student ID
- Lecturer registration with name, staff ID, and lecturer code
- Password hashing
- Login/logout using Flask sessions
- Student dashboard
- Lecturer dashboard with the registered-student list
- JSON persistence for an overnight MVP

This step deliberately does **not** add QR generation or attendance recording. Those should call the blockchain classes from Step 1 in the next step.

## Structure

```text
attendance_step_2/
├── app.py
├── config.py
├── demo_step_two.py
├── requirements.txt
├── controllers/
│   ├── auth_controller.py
│   └── dashboard_controller.py
├── domain/
│   └── users.py
├── repositories/
│   └── user_repository.py
├── services/
│   └── auth_service.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── lecturer_dashboard.html
│   └── student_dashboard.html
└── data/
    └── users.json
```

## Run it

From this folder:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python demo_step_two.py
python app.py
```

Then open `http://127.0.0.1:5000`.

Default lecturer registration code:

```text
LECTURER-DEMO
```

You can replace it before starting the app:

```powershell
$env:LECTURER_REGISTRATION_CODE="your-code"
$env:SECRET_KEY="a-long-random-value"
python app.py
```

## How it connects to Step 1 later

Step 3 should add a lecture service and controller. The service will receive the Step 1 blockchain object as a dependency and call methods such as `create_lecture(...)` and later `record_attendance(...)`. Keeping controllers, services, repositories, and domain objects separate avoids putting blockchain code directly inside Flask routes.
