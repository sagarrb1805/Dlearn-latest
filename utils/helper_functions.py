from sklearn.metrics.pairwise import cosine_similarity
import sqlitecloud
from db.db import get_db_connection, close_db_connection

from sentence_transformers import SentenceTransformer
search_model = SentenceTransformer('all-MiniLM-L6-v2')

# Lazy-loaded to avoid loading ~400MB model at startup (causes OOM on Render free tier)
# _search_model = None

# def get_search_model():
#     global _search_model
#     if _search_model is None:
#         from sentence_transformers import SentenceTransformer
#         _search_model = SentenceTransformer('all-MiniLM-L6-v2')
#     return _search_model

def get_lesson_list():
    lessons = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lesson FROM topic
        """)
        lessons = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    lessons = list(set([lesson for lesson in lessons if lesson[0] is not None]))


    response = [] # {"name": "HTML", "description": "Html description"}
    for lesson in lessons:
        lesson_dict = {
            "name": lesson[0]
        }
        response.append(lesson_dict)
    return response


def get_topic_list(lesson_name=None):
    topics = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT topic_name, description FROM topic WHERE lesson = ? ORDER BY topic_order IS NULL, topic_order ASC
                            """, (lesson_name, ))
        topics = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)

    response = [] # {"name": "HTML", "description": "Html description"}
    for topic in topics:
        topic_dict = {
            "name": topic[0],
            "description": topic[1]
        }
        response.append(topic_dict)
    return response

def fetch_topic_specific_videos(topic_name):
    
    

    videos = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f'''
                SELECT title, subject, module_name, subtopic, description, urlUpload1 as url, file_filename, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, grade, stream,video_filename, file_filename
                FROM videos
                WHERE topic = ?
                            ''', (topic_name, ))
        videos = cursor.fetchall()
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
    return videos

def fetch_video_data():
    videos = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, subject, module_name, subtopic, description, urlUpload1 as url, file_filename, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, grade, stream,video_filename, file_filename
        FROM videos
        """)
        videos = cursor.fetchall()
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
    return videos

def semantic_search_videos(query, top_k=10, topic=None):
    if(topic):
        print("inside topic search topic : ", topic)
        rows = fetch_topic_specific_videos(topic)
        print(len(rows), " rows fetched for topic : ", topic)
    else:
        rows = fetch_video_data()
    
    texts = []
    valid_rows = []

    for row in rows:
        combined = ' '.join([str(col) for col in row[:5] if col])
        if combined.strip():
            texts.append(combined)
            valid_rows.append(row)

    if not texts:
        return []

    # search_model = get_search_model()
    query_embedding = search_model.encode([query])
    text_embeddings = search_model.encode(texts)

    similarities = cosine_similarity(query_embedding, text_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    results = [valid_rows[i] for i in top_indices] 
    # results = valid_rows
    return results





def get_total_interaction_time():
    interaction = []
    response = {}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT SUM(timespend) as total_time_spent
            FROM user_interactions'''
            )
        interaction = cursor.fetchone()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)

    return interaction


def get_total_user_data():
    users = []
    # response = {}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # SELECT
        #         ui.interaction_id,
        #         ui.course_id,
        #         ui.user_id,
        #         ui.enrollment_id,
        #         ui.lessonid,
        #         ui.course_status,
        #         ui.interaction_type,
        #         v.title,
        #         v.grade,
        #         v.stream,
        #         v.subject,
        #         v.module_name,
        #         v.subtopic,
        #         v.description,
        #         v.video_filename,
        #         v.file_filename,
        #         v.urlUpload1,
        #         u.username,
        #         u.email
        #     FROM  
        #         user_interactions ui
        #     JOIN
        #         videos v ON ui.course_id = v.id
        #     JOIN
        #         users u ON ui.user_id = u.id
        #     WHERE
        #         ui.user_id = ?
        #         AND ui.course_status <> 'completed'

        cursor.execute(f'''
            SELECT u.id, u.username, u.email, up.dob
            FROM users u
            JOIN user_profile up ON u.id = up.id
                       '''
            )
        users = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")   
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)

    return users