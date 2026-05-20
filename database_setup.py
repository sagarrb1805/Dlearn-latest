import sqlite3
import sqlitecloud
from db.db import get_db_connection, close_db_connection

def init_db():
    # with sqlitecloud.connect('sqlitecloud://cqc1o5epnk.g1.sqlite.cloud:8860?apikey=HpND7AUzYbPU4EbIonwQG0vYys4XmfYSzCg6vjn3GOA') as conn:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Drop existing tables if they exist
        # c.execute('DROP TABLE IF EXISTS users')
        # c.execute('DROP TABLE IF EXISTS videos')
        c.execute('DROP TABLE IF EXISTS accessibility_data')
        c.execute('DROP TABLE IF EXISTS users')
        c.execute('DROP TABLE IF EXISTS roles')
        c.execute('DROP TABLE IF EXISTS user_profile')
        c.execute('DROP TABLE IF EXISTS dhh_profile')
        c.execute('DROP TABLE IF EXISTS language_proficiency')
        c.execute('DROP TABLE IF EXISTS tech_challenges')
        c.execute('DROP TABLE IF EXISTS learning_content_preference')
        c.execute('DROP TABLE IF EXISTS academic')
        c.execute('DROP TABLE IF EXISTS streams')
        c.execute('DROP TABLE IF EXISTS subjects')
        c.execute('DROP TABLE IF EXISTS modules')
        c.execute('DROP TABLE IF EXISTS lo_types')
        c.execute('DROP TABLE IF EXISTS urls')
        c.execute('DROP TABLE IF EXISTS lessons')
        c.execute('DROP TABLE IF EXISTS enrollments')
        c.execute('DROP TABLE IF EXISTS user_interactions')
        c.execute('DROP TABLE IF EXISTS user_ratings')
        c.execute('DROP TABLE IF EXISTS videos')

        # Create new tables

        # User Table
       
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
                communication_mode TEXT,
                importance INTEGER,
                FOREIGN KEY (id) REFERENCES user_profile(id)
            )
        ''')


        # Academic Table
        c.execute('DROP TABLE IF EXISTS academic')
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
        c.execute('DROP TABLE IF EXISTS urls')
        c.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                url_id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                accessibility_type TEXT NOT NULL
            )
        ''')
        #error fix cheythu , teams callinnu iranghtta ,ninne call cheythitt kittunnilla, call me when u r back
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
                # FOREIGN KEY (accessibility_id) REFERENCES accessibility_data(accessibility_id) last line from lessson table

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
                course_id INTEGER,
                user_id INTEGER,
                enrollment_id INTEGER,
                lessonid INTEGER,
                course_status TEXT,
                interaction_type TEXT,
                timespend DOUBLE DEFAULT 0.0, 
                no_of_clicks INT DEFAULT 0,
                rating INT,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
                FOREIGN KEY (lessonid) REFERENCES lessons(lessonid),
                FOREIGN KEY (course_id) REFERENCES videos(id),
                FOREIGN KEY (user_id) REFERENCES  users(id)
                  
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

        c.execute('DROP TABLE IF EXISTS videos')
        c.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                title TEXT NULL,
                grade TEXT NULL,
                stream TEXT NULL,
                subject TEXT NULL,
                module_name TEXT NULL,
                subtopic TEXT NULL,
                description TEXT NULL,
                urlUpload1 TEXT NULL,
                urltype TEXT NULL,
                format TEXT NULL,
                interactive_level TEXT NULL,
                difficulty_level TEXT NULL,
                accessibility1 TEXT NULL,
                video_filename TEXT NULL,
                file_filename TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INTEGER DEFAULT 0, 
                deafness_suitability TEXT NULL,
                communication_mode TEXT NULL,
                auditory DOUBLE NULL,
                kinesthetic DOUBLE NULL,
                read_write DOUBLE NULL,
                visual DOUBLE NULL
                  
                
            )
        ''')
            #url_id INTEGER,
             #   url_id2 INTEGER,
               # FOREIGN KEY (url_id) REFERENCES urls(url_id),
                #FOREIGN KEY (url_id2) REFERENCES urls(url_id)
        conn.commit()
        c.close()
        close_db_connection(conn)
if __name__ == '__main__':
    init_db()
