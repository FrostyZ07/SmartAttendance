## Smart Attendance (Streamlit + Face Recognition + Supabase)

A Python-based smart attendance system using face recognition. Admin can register students with an image, mark attendance via webcam in real-time, and view/export records. Data and images are stored in Supabase.

### Features
- Admin login to a Streamlit dashboard
- Register students (name + image)
- Real-time attendance via webcam (OpenCV + face_recognition)
- View attendance by date/student and export CSV
- Supabase for database and storage

### Tech Stack
- Python, Streamlit
- OpenCV, face_recognition (dlib)
- Supabase (Postgres + Storage)
- Pandas for CSV export

### Project Structure
```
/smart_attendance
  ├─ main.py                      # Streamlit app
  ├─ requirements.txt             # Python dependencies
  ├─ __init__.py
  └─ utils/
       ├─ db.py                   # Supabase CRUD
       ├─ face_utils.py           # Face encoding/matching utilities
       └─ __init__.py
```

### Prerequisites
- Windows 10/11 (x64)
- Python 3.11 (recommended). 3.13 may require compiling dlib.
- Webcam access

### Setup (Windows PowerShell)
1) Clone or open the project folder
```powershell
cd "C:\Smart Attendance"
```

2) Create and activate a virtual environment
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

3) Install dependencies
```powershell
pip install -r smart_attendance/requirements.txt
```
If you face issues installing dlib/face_recognition on Windows, see Troubleshooting below.

4) Create environment file
Create `smart_attendance/.env` and fill in your values:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_me
STORAGE_BUCKET=students
```
Note: Using the service role key is the quickest path while developing because it bypasses RLS.

5) Run the app
```powershell
streamlit run smart_attendance/main.py
```
`

### Usage
- Login with the admin username/password from `.env`
- Register Student: enter a name and upload a clear photo with exactly one face
- Load Known Encodings, then Start Attendance to use the webcam and auto-mark presence (once per day)
- View Reports: filter by date or student and Export CSV

### Notes
- Face encodings are stored locally in `smart_attendance/utils/encodings.json` (MVP) for fast matching. We can migrate encodings to Supabase later if needed.
- The app adds the project root to `sys.path` to ensure imports work when running via Streamlit.

### Future Improvements

#### Enhanced Features
- **Multi-face detection**: Allow registering multiple students in one image
- **Attendance status**: Add "late", "absent", "excused" statuses
- **Bulk operations**: Import students from CSV, bulk attendance marking
- **Notifications**: Email/SMS alerts for absent students
- **Analytics**: Attendance trends, charts, and reports
- **Mobile app**: React Native or Flutter app for students to self-mark attendance

#### Technical Enhancements
- **Face encoding storage**: Move encodings to Supabase for multi-device sync
- **Better face recognition**: Use deep learning models (FaceNet, ArcFace) for improved accuracy
- **Real-time sync**: WebSocket updates for live attendance tracking
- **Caching**: Redis for faster face matching with large datasets
- **API endpoints**: RESTful API for mobile app integration
- **Authentication**: Supabase Auth with role-based access (admin, teacher, student)

#### UI/UX Improvements
- **Dark mode**: Toggle between light/dark themes
- **Responsive design**: Better mobile and tablet support
- **Progress indicators**: Loading states for face processing
- **Error handling**: Better error messages and recovery
- **Accessibility**: Screen reader support, keyboard navigation
- **Internationalization**: Multi-language support

#### Security & Performance
- **Rate limiting**: Prevent abuse of face recognition API
- **Image compression**: Optimize storage and processing speed
- **Backup system**: Automated database backups
- **Logging**: Comprehensive audit logs for attendance changes
- **Data privacy**: GDPR compliance, data retention policies
- **Encryption**: Encrypt sensitive data at rest

#### Deployment & DevOps
- **Docker**: Containerize the application
- **CI/CD**: Automated testing and deployment
- **Monitoring**: Health checks, performance metrics
- **Scaling**: Load balancing for multiple instances
- **Environment management**: Separate dev/staging/prod configs

#### Integration Possibilities
- **LMS integration**: Connect with Canvas, Moodle, etc.
- **Calendar sync**: Google Calendar, Outlook integration
- **HR systems**: Connect with employee management systems
- **Biometric devices**: Integrate with fingerprint/ID card readers
- **IoT sensors**: Motion sensors, door access systems

### Troubleshooting (Windows)
- NumPy/Pandas wheels
  - If you see messages about building NumPy from source, ensure 64‑bit Python and upgrade pip:
    ```powershell
    python -m pip install --upgrade pip setuptools wheel
    ```
- dlib/face_recognition install errors
  - Quickest: use Python 3.11 x64 and prebuilt wheels. Some setups can use `dlib-bin`.
  - If `dlib-bin` isn't available, install build tools and compile:
    1) Install CMake (x64) from `https://cmake.org/download/` and choose "Add to PATH". Verify with `cmake --version`.
    2) Install Visual Studio Build Tools 2022 with workload "Desktop development with C++" (MSVC v143, Windows 10/11 SDK). Verify `cl` in a new terminal.
    3) Then in your venv:
       ```powershell
       pip install --upgrade pip setuptools wheel cmake
       pip install dlib
       pip install face_recognition==1.3.0
       ```
- RLS errors on insert (Unauthorized / violates row-level security)
  - Use Service Role key in `.env` during development, or add the permissive RLS policies above.
- Webcam not accessible
  - Close other camera apps. If needed, change camera index in code from `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`.

### License
This project is provided as-is for educational purposes.
