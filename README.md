# qr-attendance-project
Working demo of proposed project for a college course. The main idea was using a main camera to quickly scan students' QR codes to mark them as present in lectures. However, due to time constraints, the scope was scaled-down and it became a simple QR codes scanned by students to mark themselves present rather than the reverse. 

Ultimately, the team decided to move on with another project idea so the development stopped.

## How to Run
Install python3 if not installed already.
1. Download the repo
2. Open the folder ```qr-attendance-project``` inside the IDE of your choice such as VS Code.
3. In the terminal inside the IDE, run ```pip install -r requirements.txt``` or inside a venv if you like.
4. run the file ```"Web integration"/app.py```
5. Inside the terminal you will find these lines. 
```
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.8.101:5000
```
6. Open the 127.x.x.x on your desktop browser.
7. Open the 192.x.x.x on your phone's browser.
8. Now, you can register an account from your phone's browser and create lectures with their QR codes from the desktop browser.

## Screenshots
![Desktop Website](/screenshots/desktop-website-lecturer-add-lecture.png)
![Desktop Website. An expired QR code for a lecture](/screenshots/desktop-website-expired-qr-lecture.png)
![Mobile website. A student attendance log](/screenshots/mobile-website-student-attendance-log.jpg)
![Mobile website. A student cofirmation of attendance screen](/screenshots/mobile-website-student-confirm-attendance.jpg)
