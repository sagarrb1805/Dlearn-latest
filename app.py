from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
from routes.test_route import test_bp
from routes.student_route import student_route_bp
from routes.resource_route import resource_bp
import sqlitecloud

from utils.common import Common, get_user_membership
from utils.recommendation import FuzzyClustering, filter_resources, rank_resources
from utils.helper_functions import get_topic_list, fetch_video_data, get_total_interaction_time, get_total_user_data, get_lesson_list
from db.db import get_db_connection, close_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

app.register_blueprint(test_bp, url_prefix='/test')
app.register_blueprint(student_route_bp)
app.register_blueprint(resource_bp)


# Ensure the upload folder existsqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    with sqlite3.connect('learning_websiteee.db') as conn:
        c = conn.cursor() 
        # Drop existing tables if needed
        # c.execute('DROP TABLE IF EXISTS users')
        # c.execute('DROP TABLE IF EXISTS roles')
        # c.execute('DROP TABLE IF EXISTS user_profile')
        # c.execute('DROP TABLE IF EXISTS dhh_profile')
        # c.execute('DROP TABLE IF EXISTS language_proficiency')
        # c.execute('DROP TABLE IF EXISTS tech_challenges')
        # c.execute('DROP TABLE IF EXISTS learning_content_preference')
        # c.execute('DROP TABLE IF EXISTS academic')
        # c.execute('DROP TABLE IF EXISTS streams')
        # c.execute('DROP TABLE IF EXISTS subjects')
        # c.execute('DROP TABLE IF EXISTS modules')
        # c.execute('DROP TABLE IF EXISTS lo_types')
        # c.execute('DROP TABLE IF EXISTS accessibility_data')
        # c.execute('DROP TABLE IF EXISTS lessons')
        # c.execute('DROP TABLE IF EXISTS enrollments')
        # c.execute('DROP TABLE IF EXISTS user_interactions')
        # c.execute('DROP TABLE IF EXISTS user_ratings')

        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                password TEXT NOT NULL,
                last_login_date TEXT,
                date_joined TEXT
            )
        ''')

        # Role Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY,
                role TEXT UNIQUE NOT NULL
            )
        ''')

        # User Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                dob DATE NOT NULL,
                gender TEXT,
                grade TEXT,
                stream TEXT,
                reason TEXT,
                medium TEXT,
                prof INTEGER,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')

        # DHH Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS dhh_profile (
                id INTEGER PRIMARY KEY,
                per INTEGER,
                degree TEXT,
                type TEXT,
                stbelow TEXT,
                stabove TEXT,
                imprv INTEGER,
                haid TEXT,
                implant TEXT,
                cmode TEXT,
                lipread TEXT,
                profilp TEXT,
                history TEXT,
                relation TEXT,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')

        # Language Proficiency Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS language_proficiency (
                id INTEGER PRIMARY KEY,
                english_proficiency TEXT,
                written_english INTEGER,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')

        # Tech Challenges Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS tech_challenges (
                id INTEGER PRIMARY KEY,
                challenges TEXT,
                frequency TEXT,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')

        # Learning Content Preference Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS learning_content_preference (
                id INTEGER PRIMARY KEY,
                learning_style TEXT,
                accessibility_feature TEXT,
                importance INTEGER,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')

        # Academic Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS academic (
                id INTEGER PRIMARY KEY,
                schooling TEXT,
                mixedexp TEXT,
                marks_10 INTEGER,
                marks_11 INTEGER,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')

        # Stream Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                streamid INTEGER PRIMARY KEY,
                stream TEXT NOT NULL,
                grade TEXT
            )
        ''')

        # Subject Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subjectid INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                description TEXT,
                userid INTEGER,
                streamid INTEGER,
                FOREIGN KEY (userid) REFERENCES users(id),
                FOREIGN KEY (streamid) REFERENCES streams(streamid)
            )
        ''')

        # Module Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                moduleid INTEGER PRIMARY KEY,
                module_name TEXT NOT NULL,
                subjectid INTEGER,
                topic TEXT,
                description TEXT,
                position INTEGER,
                completion_criteria TEXT,
                FOREIGN KEY (subjectid) REFERENCES subjects(subjectid)
            )
        ''')

        # LO Type Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS lo_types (
                loid INTEGER PRIMARY KEY,
                lotype TEXT,
                resource_url TEXT,
                lo_description TEXT,
                tags TEXT,
                duration TEXT,
                complexity TEXT
            )
        ''')

        # Accessibility Data Table
        # c.execute('''
        #     CREATE TABLE IF NOT EXISTS accessibility_data (
        #         accessibility_id INTEGER PRIMARY KEY,
        #         accessibility_type TEXT
        #     )
        # ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                url_id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                accessibility_type TEXT NOT NULL

            )
        ''')


     # Lesson Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                lessonid INTEGER PRIMARY KEY,
                moduleid INTEGER,
                topic TEXT,
                subtopic TEXT,
                position INTEGER,
                loid INTEGER,
                accessibility_id INTEGER,
                completion_criteria TEXT,
                glossary TEXT,
                FOREIGN KEY (moduleid) REFERENCES modules(moduleid),
                FOREIGN KEY (loid) REFERENCES lo_types(loid)
            )
        ''')
                # FOREIGN KEY (accessibility_id) REFERENCES accessibility_data(accessibility_id)


        # Enrollment Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                userid INTEGER,
                subjectid INTEGER,
                progress TEXT,
                rating INTEGER,
                FOREIGN KEY (userid) REFERENCES users(id),
                FOREIGN KEY (subjectid) REFERENCES subjects(subjectid)
            )
        ''')

        # User Interaction Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                interaction_id INTEGER PRIMARY KEY,
                enrollment_id INTEGER,
                lessonid INTEGER,
                interaction_type TEXT,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
                FOREIGN KEY (lessonid) REFERENCES lessons(lessonid)
            )
        ''')

        # User Rating Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_ratings (
                rating_id INTEGER PRIMARY KEY,
                enrollment_id INTEGER,
                rating INTEGER,
                rated_time TEXT,
                comments TEXT,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                grade TEXT NOT NULL,
                stream TEXT NOT NULL,
                subject TEXT NOT NULL,
                module_name TEXT NOT NULL,
                subtopic TEXT NOT NULL,
                description TEXT NOT NULL,
                urlUpload1 TEXT NOT NULL,
                urltype TEXT NOT NULL,
                format TEXT NOT NULL,
                interactive_level TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                accessibility1 TEXT NOT NULL,
                video_filename TEXT NOT NULL,
                file_filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0

            )
        ''')
        conn.commit()

        # Create new tables
        # (Refer to the database_setup.py for the new schema creation code)
        # ... (Include the schema creation code from database_setup.py)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('student_signin.html')



@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect('learning_websiteee.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO users (email, username, role, password) VALUES (?, ?, ?, ?)',
                      (email, username, 'admin', password))
            conn.commit()
        return redirect(url_for('admin_login'))
    return render_template('admin_signup.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = None
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
                      (username, password, 'admin'))
            user = cursor.fetchone()
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)
        # with sqlite3.connect('learning_websiteee.db') as conn:
        #     c = conn.cursor()
        #     c.execute('SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
        #               (username, password, 'admin'))
        #     user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            session['role'] = 'admin'
            return redirect(url_for('dashboard'))
    return render_template('admin_login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    
    # if request.method == 'POST':
    #     try:
            # print("form submit ")
            # topic = request.form.get('topic', '')
            # grade = request.form.get('grade', '')
            # stream = request.form.get('stream', '')
            # subject = request.form.get('subject', '')
            # module_name = request.form.get('moduleName', '')
            # subtopic = request.form.get('subtopic', '')
            # description = request.form.get('description', '')

            # # Convert checkbox lists to comma-separated strings
            # accessibility1 = ', '.join(request.form.getlist('accessibility1[]'))
            # urltype = ', '.join(request.form.getlist('urltype[]'))

            # format = request.form.get('format', '')
            # interactive_level = request.form.get('interactive_level', '')
            # difficulty_level = request.form.get('difficulty_level', '')
            # urlUpload1 = request.form.get('urlUpload1', '')

            
            # print("before getting video files ")
            # video = request.files.get('video_filename')
            # file = request.files.get('file_filename')
            # print("after getting video files ")
            # deafness_suitability = request.form.get("deafness_suitability")
            # communication_mode = request.form.get('communication_mode')

            # auditory = request.form.get('auditory')
            # kinesthetic = request.form.get('kinesthetic')
            # read_write = request.form.get('read_write')
            # visual = request.form.get('visual')
            # print("after getting new datas ")

            # video_filename = ''
            # file_filename = ''

            # # Check if video file exists before accessing its filename
            # if video and video.filename:
            #     video_filename = secure_filename(video.filename)
            #     video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
            #     video.save(video_filepath)

            # # Check if file exists before accessing its filename
            # if file and file.filename:
            #     file_filename = secure_filename(file.filename)
            #     file_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_filename)
            #     file.save(file_filepath)
            
            # conn = get_db_connection()
            # try:
            #     cursor = conn.cursor()
            #     cursor.execute('''
            #     INSERT INTO videos (
            #         title, grade, stream, subject, module_name, subtopic, description, accessibility1, video_filename, file_filename, urltype, format, interactive_level, difficulty_level, urlUpload1, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual) 
            #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #         ''', ( topic, grade, stream, subject, module_name, subtopic, description, accessibility1, video_filename, file_filename, urltype, format, interactive_level, difficulty_level, urlUpload1, deafness_suitability,communication_mode, auditory, kinesthetic, read_write, visual))
            #     conn.commit()
            # except sqlitecloud.Error as e:
            #     print(f"Database error: {e}")
            #     if conn:
            #         conn.rollback()
            # finally:
            #     if 'cursor' in locals() and cursor:
            #         cursor.close()
            #     close_db_connection(conn)
            # cursor = conn.cursor()
            # print('form submit before db ')
            # cursor.execute('''
            #     INSERT INTO videos (
            #         topic, grade, stream, subject, module_name, subtopic, description, accessibility1, video_filename, file_filename, urltype, format, interactive_level, difficulty_level, urlUpload1, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual) 
            #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #         ''', ( topic, grade, stream, subject, module_name, subtopic, description, accessibility1, video_filename, file_filename, urltype, format, interactive_level, difficulty_level, urlUpload1, deafness_suitability,communication_mode, auditory, kinesthetic, read_write, visual))
            # conn.commit()
            # cursor.close()
            # conn.close()
            # print("form submit after db")
            
        #     return redirect(url_for('dashboard'))
        # except Exception as e:
        #     print("exception in material addition : ", e)
    
    return render_template('dashboard.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        dob = request.form['dob']
        gender = request.form['gender']
        grade = request.form['grade']
        stream = request.form['stream']
        reason = request.form.getlist('reason')
        medium = request.form['medium']
        prof = request.form['prof']
        schooling = request.form['schooling']
        mixedexp = request.form['mixedexp']
        marks_10 = request.form['marks_10']
        marks_11 = request.form['marks_11']
        per = request.form['per']
        degree = request.form['degree']
        type = request.form['type']
        stbelow = request.form['stbelow']
        stabove = request.form['stabove']
        imprv = request.form['imprv']
        haid = request.form['haid']
        implant = request.form['implant']
        cmode = request.form['cmode']
        lipread = request.form['lipread']
        profilp = request.form['profilp']
        history = request.form['history']
        relation = request.form['relation']
        english_proficiency = request.form['english_proficiency']
        written_english = request.form['written_english']
        communication_mode = request.form.getlist('communication_mode')
        accessibility_feature = request.form.getlist('accessibility_feature')
        learning_style = request.form.getlist('learning_style')
        importance = request.form['importance']
        challenges = request.form.getlist('challenges')
        frequency = request.form['frequency']


        # (Include all other fields and handle accordingly)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (email, username, role, password) VALUES (?, ?, ?, ?)
            ''', (email, username, 'student', password ))
            user_id = cursor.lastrowid  # Get the ID of the newly created user
            cursor.execute('''
                INSERT INTO user_profile (id, username, dob, gender, grade, stream, reason, medium, prof) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, dob, gender, grade, stream, ','.join(reason), medium, prof))
            cursor.execute('''
                INSERT INTO academic (id, schooling, mixedexp, marks_10, marks_11) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, schooling, mixedexp, marks_10, marks_11))
            cursor.execute('''
                INSERT INTO dhh_profile (id, per, degree, type, stbelow, stabove, imprv, haid, implant, cmode, lipread, profilp, history, relation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, per, degree, type, stbelow, stabove, imprv, haid, implant, cmode, lipread, profilp, history, relation))
            cursor.execute('''
                INSERT INTO language_proficiency (id, english_proficiency, written_english) VALUES (?, ?, ?)
            ''', (user_id, english_proficiency, written_english))
            cursor.execute('''
                INSERT INTO learning_content_preference (id, learning_style, accessibility_feature, communication_mode, importance) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, ','.join(learning_style), ','.join(accessibility_feature), ','.join(communication_mode) , importance))
            cursor.execute('''
                INSERT INTO tech_challenges (id, challenges, frequency) VALUES (?, ?, ?)
            ''', (user_id, ','.join(challenges), frequency))
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)
        
        # with sqlite3.connect('learning_websiteee.db') as conn:
        #     c = conn.cursor()
        #     c.execute('''
        #         INSERT INTO users (email, username, role, password) VALUES (?, ?, ?, ?)
        #     ''', (email, username, 'student', password ))
        #     user_id = c.lastrowid  # Get the ID of the newly created user
        #     c.execute('''
        #         INSERT INTO user_profile (id, username, dob, gender, grade, stream, reason, medium, prof) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        #     ''', (user_id, username, dob, gender, grade, stream, ','.join(reason), medium, prof))
        #     c.execute('''
        #         INSERT INTO academic (id, schooling, mixedexp, marks_10, marks_11) VALUES (?, ?, ?, ?, ?)
        #     ''', (user_id, schooling, mixedexp, marks_10, marks_11))
        #     c.execute('''
        #         INSERT INTO dhh_profile (id, per, degree, type, stbelow, stabove, imprv, haid, implant, cmode, lipread, profilp, history, relation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        #     ''', (user_id, per, degree, type, stbelow, stabove, imprv, haid, implant, cmode, lipread, profilp, history, relation))
        #     c.execute('''
        #         INSERT INTO language_proficiency (id, english_proficiency, written_english) VALUES (?, ?, ?)
        #     ''', (user_id, english_proficiency, written_english))
        #     c.execute('''
        #         INSERT INTO learning_content_preference (id, learning_style, accessibility_feature, importance) VALUES (?, ?, ?, ?, ?)
        #     ''', (user_id, ','.join(learning_style), ','.join(accessibility_feature), ','.join(communication_mode) , importance))
        #     c.execute('''
        #         INSERT INTO tech_challenges (id, challenges, frequency) VALUES (?, ?, ?)
        #     ''', (user_id, ','.join(challenges), frequency))
        #     conn.commit()

        return redirect(url_for('home'))
    return render_template('student_signup.html')

# @app.route('/student_signin', methods=['GET', 'POST'])
# def student_signin():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         with sqlite3.connect('learning_websiteee.db') as conn:
#             c = conn.cursor()
#             c.execute('SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
#                       (username, password, 'student'))
#             user = c.fetchone()
#             if user:
#                 session['user_id'] = user[0]
#                 session['role'] = 'student'
#                 return redirect(url_for('home'))
#     return render_template('student_signin.html')

@app.route('/home')
def home():
    print("topics : ", get_lesson_list())
    lessons = get_lesson_list() #[{"name": "HTML", "description": "Html description"}, {"name": "CSS", "description": "Css description"}, {"name": "JavaScript", "description": "JavaScript description"}]
    try:
        user_profile_data=None
        user_data = None
        if 'user_id' not in session:
            return redirect(url_for('index'))
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE id=?
            ''',(session.get("user_id"),))
            user_profile_data = cursor.fetchone()
            # print("videos : ", videos)
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)

        conn = get_db_connection()   
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                dh.degree, 
                lp.accessibility_feature,
                lp.communication_mode
            FROM  
                dhh_profile dh
            JOIN
                learning_content_preference lp ON dh.id = lp.id
            WHERE
                dh.id = ?
                AND lp.id = ?
            ''', (session.get("user_id"), session.get("user_id")))
            user_data = cursor.fetchall()
            print("user_data : ", user_data)
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)
        learner_profile = {
        'Accessibility': user_data[0][1].split(','), 
        'DeafnessProfile': user_data[0][0], 
        'CommunicationMode': user_data[0][2].split(',')
    }
        # print("user learning profile : ", learner_profile)
        learner_pref = get_user_membership(session.get("user_id"))
        # print("learner_pref", learner_pref)
        # print("videos: ", videos)
        # print("video[0]: ", videos[0])
        filterd_resources = filter_resources(learner_profile, [])
        # print("filter resource: ", filterd_resources[:2])
        print(len(filterd_resources))
        ranked_resources = []
        if(len(filterd_resources) != 0):
            ranked_resources = rank_resources(filterd_resources, learner_pref)
        else:
            ranked_resources = []
        # print("ranked_resources resources: ", ranked_resources[:2])
        return render_template('home.html', videos=ranked_resources, user_profile_data=user_profile_data, lessons=lessons)
    except Exception as e:
        print("exception in home page: ", e)
        return render_template('home.html', videos=[], lessons=lessons)

# @app.route('/home')
# def home():
#     if 'user_id' not in session:
#         return redirect(url_for('index'))
#     with sqlite3.connect('learning_websiteee.db') as conn:
#         c = conn.cursor()
#         c.execute('''
#             SELECT topic, grade, stream, subject, module_name, subtopic, description, video_filename, file_filename 
#             FROM videos
#         ''')
#         videos = c.fetchall()
#     return render_template('home.html', videos=videos)


# @app.route('/studentdetails')
# def studentdetails():
#     return render_template('studentdetails.html')

# @app.route('/api/students', methods=['GET'])
# def get_students():
#     conn = sqlite3.connect('learning_websiteee.db')
#     c = conn.cursor()
#     c.execute('''
#         SELECT up.id, u.username, u.email, up.dob, up.gender, up.grade
#         FROM users u
#         JOIN user_profile up ON u.username = up.username
#         WHERE u.role = "student"
#     ''')
#     students = c.fetchall()
    

#     conn.close()
#     return jsonify([dict(student) for student in students])


def row_to_dict(cursor, row):
    """
    Convert a SQLite row to a dictionary using the cursor description.
    """
    return {cursor.description[idx][0]: value for idx, value in enumerate(row)}

@app.route('/studentdetails')
def studentdetails():
    videos_count = len(fetch_video_data())
    return render_template('studentdetails.html', videos_count=videos_count, total_interaction_time=get_total_interaction_time(), full_user_data=get_total_user_data())

@app.route('/api/students', methods=['GET'])
def get_students():
    conn = sqlite3.connect('learning_websiteee.db')
    conn.row_factory = sqlite3.Row  # Enable column name access in rows
    c = conn.cursor()

    # Execute the SQL query to fetch the data
    c.execute('''
        SELECT up.id, u.username, u.email, up.dob, up.gender, up.grade
        FROM users u
        JOIN user_profile up ON u.username = up.username
        WHERE u.role = "student"
    ''')

    students = c.fetchall()
    students_list = []

    for student in students:
        # Convert each row to a dictionary
        student_dict = {
            'id': student['id'],
            'username': student['username'],
            'email': student['email'],
            'dob': student['dob'],
            'gender': student['gender'],
            'grade': student['grade']
        }
        students_list.append(student_dict)

    conn.close()
    return jsonify(students_list)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# more button functionality topic page
# @app.route('/recommended_load_more')
# def recommended_load_more():
#     start = int(request.args.get("start", 0))
#     videos = get_recommended_videos()[start:start+20]
#     return render_template("partials/recommended_items.html", videos=videos)

# @app.route('/available_load_more')
# def available_load_more():
#     start = int(request.args.get("start", 0))
#     videos = get_available_videos()[start:start+20]
#     return render_template("partials/available_items.html", videos=videos)


if __name__ == '__main__':
    Common.model = FuzzyClustering("./files/DHHTrainDataPre.csv", n_clusters=6)
    app.run(debug=True)

# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)
