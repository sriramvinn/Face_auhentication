from flask import Flask, render_template, request, redirect, url_for, g, session
from deepface import DeepFace
import cv2
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'


if not os.path.exists('registered_faces/'):
    try:
        os.mkdir('registered_faces/')
    except OSError:
        print('Error creating directory: registered_faces/')

DATABASE = 'users.db'

# Connect to the SQLite database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Create the users table if it doesn't exist
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                userid TEXT,
                password TEXT
            )
        ''')
        db.commit()

# Initialize the database
init_db()

# Home page
@app.route('/', methods=['GET', 'POST'])
def home():
    error = None

    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            
            # Authenticate user using credentials
            if authenticate_user(username, password):
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid username or password'

        elif 'face_login' in request.form:
            # Perform face login
            if face_login():
                return redirect(url_for('dashboard'))
            else:
                error = 'Face verification failed.'

    return render_template('index.html', error=error)


# Sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        userid = request.form['userid']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Verify if passwords match
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match!')

        # Register user
        if register_user(username, userid, password):
            return redirect(url_for('home'))
        else:
            return render_template('signup.html', error='User ID already exists!')
    
    return render_template('signup.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return render_template('dashboard.html', username='username')

# Authenticate user using credentials
def authenticate_user(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user:
        stored_password = user[3]
        if password == stored_password:
            return True

    return False

# Perform face login
def face_login():
    # Capture face image from webcam
    video_capture = cv2.VideoCapture(0)
    capture_face = False
    temp = 0

    if not os.path.exists('registered_faces/'):
        os.makedirs('registered_faces/')

    while True:
        ret, frame = video_capture.read()
        cv2.imshow('Face Login', frame)

        # Detect face and perform face recognition
        faces = []
        try:
            faces = DeepFace.detectFace(frame, detector_backend='opencv')
        except:
            faces = []

        if len(faces) > 0 and not capture_face:
            cv2.imwrite('temp_face_image.jpg', frame)
            capture_face = True

        if 0xFF == ord('q') or capture_face:
            break

    video_capture.release()
    cv2.destroyAllWindows()

    registered_faces_dir = os.path.join(os.getcwd(), 'registered_faces')
    if not os.path.exists(registered_faces_dir):
        return False

    result = DeepFace.verify('temp_face_image.jpg', registered_faces_dir)
    print(result)

    if result > 0:
        return True
    else:
        return False


# Register user
def register_user(username, userid, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE userid = ?', (userid,))
    user = cursor.fetchone()

    if user:
        return False

    # Capture face image from webcam
    video_capture = cv2.VideoCapture(0)
    capture_face = False
    temp = 0

    while True:
        ret, frame = video_capture.read()
        cv2.imshow('Face Registration', frame)

        # Detect face and perform face recognition
        faces = []
        try:
            faces = DeepFace.detectFace(frame, detector_backend='opencv')
        except:
            faces = []
        if len(faces) > 0 and not capture_face:
            cv2.imwrite(f'registered_faces/{userid}.jpg', frame)
            capture_face = True

        if cv2.waitKey(1) or 0xFF == ord('q') or capture_face:
            break

    else:
        return False

    video_capture.release()
    cv2.destroyAllWindows()

    # Add user credentials to the database
    cursor.execute('INSERT INTO users (username, userid, password) VALUES (?, ?, ?)', (username, userid, password))
    db.commit()

    return True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)