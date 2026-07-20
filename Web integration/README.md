# Step 3 — Web Integration

This step adds a Flask web layer around the OOP blockchain and QR services.

## What works

- Student registration with name and ID.
- Lecturer lecture creation.
- Signed, expiring QR codes.
- Student lecture confirmation and an **Attend** button.
- Duplicate-attendance prevention.
- Lecture and attendance events stored in a persistent blockchain JSON file.
- Lecturer view of all students in a lecture.
- Student view of only the current student's records.
- Blockchain integrity check.

## File responsibilities

- `models.py`: domain data classes.
- `attendance_blockchain.py`: blocks, persistence, validation, and ledger queries.
- `repositories.py`: student and QR token JSON repositories.
- `qr_service.py`: token signing, validation, scan URLs, and PNG generation.
- `services.py`: use cases and validation.
- `controllers.py`: Flask lecturer and student routes.
- `app.py`: dependency construction and Flask app factory.
- `demo_step_three.py`: console smoke test.

## Install and run

From this folder:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

When the app starts, it automatically detects the host computer's active LAN IPv4 address and prints a line such as:

```text
QR attendance URL: http://192.168.1.20:5000
```

Open that address on the lecturer computer. Generated QR codes use the same LAN address rather than `127.0.0.1`.

## Testing on a phone

1. Put the laptop and phone on the same Wi-Fi network.
2. Start the application with `python app.py`.
3. Confirm the printed QR attendance URL uses the laptop's LAN address.
4. Create a lecture and scan its QR code using the phone.

To override automatic detection, set `PUBLIC_BASE_URL` before launching:

```powershell
$env:PUBLIC_BASE_URL="http://192.168.1.20:5000"
$env:ATTENDANCE_SECRET_KEY="replace-with-a-long-random-value"
python app.py
```

Windows Firewall may ask for permission. Allow Python on private networks.

## Run the console smoke test

```bash
python demo_step_three.py
```

It creates a lecture, writes a QR PNG, records one attendance, checks the chain, and proves that a duplicate is rejected.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## MVP limitations

This overnight version intentionally has no lecturer authentication, passwords, encryption setup, location checks, or camera-based identity verification. Student identity uses the browser session and registered student ID, so it is a demonstration rather than a production attendance system.
