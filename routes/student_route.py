from flask import Blueprint, request, session, redirect, render_template, url_for
import sqlite3
import sqlitecloud
from db.db import get_db_connection, close_db_connection


student_route_bp = Blueprint('student_route', __name__)




@student_route_bp.route('/create_student', methods=['POST', 'GET'])
def create_student():
    if(request.method == 'POST'):
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        grade = request.form.get('grade', '')
        stream = request.form.get('stream', '')
        reason = request.form.getlist('reason')
        medium = request.form.get('medium', '')
        prof = request.form.get('prof', '')
        schooling = request.form.get('schooling', '')
        mixedexp = request.form.get('mixedexp', '')
        marks_10 = request.form.get('marks_10', '')
        marks_11 = request.form.get('marks_11', '')
        per = request.form.get('per', '')
        degree = request.form.get('degree', '')
        type = request.form.get('type', '')
        stbelow = request.form.get('stbelow', '')
        stabove = request.form.get('stabove', '')
        imprv = request.form.get('imprv', '')
        haid = request.form.get('haid', '')
        implant = request.form.get('implant', '')
        cmode = request.form.get('cmode', '')
        lipread = request.form.get('lipread', '')
        profilp = request.form.get('profilp', '')
        history = request.form.get('history', '')
        relation = request.form.get('relation', '')
        english_proficiency = request.form.get('english_proficiency', '')
        written_english = request.form.get('written_english', '')
        communication_mode = request.form.getlist('communication_mode')
        accessibility_feature = request.form.getlist('accessibility_feature')
        learning_style = request.form.getlist('learning_style')
        importance = request.form.get('importance', '')
        challenges = request.form.getlist('challenges')
        frequency = request.form.get('frequency', '')
        print("learing_style : ", learning_style)
        print("accessibility_feature : ", accessibility_feature)
        print("communication_mode : ", communication_mode)


        # (Include all other fields and handle accordingly)
        print("Received data for new student registration:")
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
            print("Finished processing new student registration.")
        return render_template('create_student.html', addition_status = True)

    return render_template('create_student.html', addition_status = False)


@student_route_bp.route('/student_signin', methods=['POST', 'GET'])
def student_signin():
    print("inside student route: ")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = None
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ? AND password = ? AND role = ?',
                      (username, password, 'student'))
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
        #               (username, password, 'student'))
        #     user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                session['role'] = 'student'
                return redirect(url_for('home'))
    return render_template('student_signin.html')
