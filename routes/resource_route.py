from flask import Blueprint, Flask, render_template, request, redirect, url_for, jsonify, session, flash
# from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from db.db import get_db_connection, close_db_connection
import sqlitecloud
import re
import math
from urllib.parse import urlparse
from utils.common import Common, get_user_membership
from utils.recommendation import FuzzyClustering, filter_resources, rank_resources
from utils.helper_functions import semantic_search_videos, fetch_video_data, get_topic_list
from utils.user_grouping import get_data
 

resource_bp = Blueprint('resource_route', __name__)



@resource_bp.route('/all_videos', methods=['GET'])
def all_videos():
    videos = fetch_video_data()
    return jsonify(videos)

@resource_bp.route('/semantic_search', methods=['POST'])
def semantic_search():
    data = request.json
    # print("data: ", data)
    query = data.get('query')
    topic = data.get('topic')
    print("query: ", query, topic)
    response = []
    result = semantic_search_videos(query, top_k=10, topic=topic)
    print("result: ", len(result))
    # for row in result:
    # print(row)
    # print(f"Type: {type(row)}")

    # Iterate through the list by index to replace elements
    for i in range(len(result)):
        current_tuple = result[i]
        
        # Convert the tuple to a list to make it mutable for modification
        temp_list = list(current_tuple)
        
        # Check bounds before attempting to lowercase to prevent IndexError
        if len(temp_list) > 8:
            temp_list[8] = str(temp_list[8]).lower()
        if len(temp_list) > 9:
            temp_list[9] = str(temp_list[9]).lower()
        if len(temp_list) > 10:
            temp_list[10] = str(temp_list[10]).lower()
        
        # Convert the modified list back to a tuple
        result[i] = tuple(temp_list)

        
    print("result: ", result[0], "\n\n")
    # print("user_profile_recommendations(session.get('user_id'), result)",user_profile_recommendations(session.get('user_id'), result))
    recommended_from_serach = user_profile_recommendations(session.get('user_id'), result)
    print("recommended_from_serach: ", len(recommended_from_serach))
    # print("recommended_from_serach: ", recommended_from_serach[0], "\n\n")
    if(len(recommended_from_serach) == 0):  
        response = result
    else:
        response = list(set(recommended_from_serach + result))
    print("response: ", len(response))  
    # print("result: ", result)
    # rec_response = get_hybrid_recommendation(session.get("user_id"), result)
    # print("rec_response: ", rec_response)  
    return jsonify(response)

def get_user_preference(user_id):
    count = 0
    conn = get_db_connection()   
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
            COUNT(*) FROM user_interactions WHERE user_id = ? 
        ''', (user_id, ))
        count = cursor.fetchall()
        count = count[0][0]
        # print("user_data count : ", count[0][0])
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    return count

# def get_hybrid_recommendation(user_id, videos):
#     user_profile_resources = user_profile_recommendations(user_id, videos)
#     user_group_recommended_ids = get_data(user_id, 25)
#     print("user_group_recommended_ids: ", user_group_recommended_ids)
#     # print('videos: ', videos[:3])
#     user_group_recommended_videos = [video for video in videos if video[-1] in user_group_recommended_ids]
#     pass

def user_profile_recommendations(user_id, videos=[]):
    try:
        videos = videos
        user_data = None
        if user_id is None:
            return redirect(url_for('index'))
        

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
            ''', (user_id, user_id))
            user_data = cursor.fetchall()
            # print("user_data : ", user_data)
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
        user_interaction_count = get_user_preference(user_id)
        # print("user_interaction_count: ", user_interaction_count)
        if(user_interaction_count <=3):
            learner_pref = get_user_membership(user_id) #learner_pref {'Auditory': 0.31606664251378125, 'Kinesthetic': 0.3079119262012944, 'Read/Write': 0.062026319117999336, 'Visual': 0.313995112166925}
        else:
            conn = get_db_connection()   
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                    auditory, kinesthetic, read_write, visual, isl_score, voice_score, isl_voice_score, subtitle_score, caption_score, transcript_score
                    FROM users
                    WHERE id = ?
                ''', (user_id,))
                user_data = cursor.fetchone()
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
                learner_pref = {    
                    'Auditory': user_data[0],
                    'Kinesthetic': user_data[1],
                    'Read/Write': user_data[2],
                    'Visual': user_data[3]
                }
                print("learner_pref in interaction from users: ", learner_pref)
                acc_scores = {
                    'ISL only': user_data[4],
                    'Voice only': user_data[5],
                    'ISL and Voice': user_data[6],
                    'Subtitle': user_data[7],
                    'Captions': user_data[8],
                    'Transcripts': user_data[9]
                }

                top_3 = sorted(acc_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                top_3_labels = [label for label, score in top_3]
                learner_profile['Accessibility'] = top_3_labels

        # print("learner_pref: ", learner_pref)
        # user_interaction_count = get_user_preference(user_id)
        # print("videos: ", videos)
        # print("video[0]: ", videos[0])
        filterd_resources = filter_resources(learner_profile, videos)
        print("filter resourcellength: ", len(filterd_resources))
        # print(filterd_resources)
        ranked_resources = []
        if(len(filterd_resources) != 0):
            ranked_resources = rank_resources(filterd_resources, learner_pref)
        else:
            ranked_resources = []
        print("ranked_resources resources: ", len(ranked_resources))
        return ranked_resources
    except Exception as e:
        print("exception in user profile recommended page: ", e)
        return []
 

@resource_bp.route('/recommended')
def recommended():
    try:
        videos = []
        user_data = None
        if 'user_id' not in session:
            return redirect(url_for('index'))
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, grade, stream, subject, module_name, subtopic, description, video_filename, file_filename, urlUpload1 as url, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, id
            FROM videos
            ''')
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
        ranked_resources = user_profile_recommendations(session.get("user_id"), videos)[:10]

    #     conn = get_db_connection()   
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute('''
    #             SELECT
    #             dh.degree, 
    #             lp.accessibility_feature,
    #             lp.communication_mode
    #         FROM  
    #             dhh_profile dh
    #         JOIN
    #             learning_content_preference lp ON dh.id = lp.id
    #         WHERE
    #             dh.id = ?
    #             AND lp.id = ?
    #         ''', (session.get("user_id"), session.get("user_id")))
    #         user_data = cursor.fetchall()
    #         print("user_data : ", user_data)
    #         conn.commit()
    #     except sqlitecloud.Error as e:
    #         print(f"Database error: {e}")
    #         if conn:
    #             conn.rollback()
    #     finally:
    #         if 'cursor' in locals() and cursor:
    #             cursor.close()
    #         close_db_connection(conn)
    #     learner_profile = {
    #     'Accessibility': user_data[0][1].split(','), 
    #     'DeafnessProfile': user_data[0][0], 
    #     'CommunicationMode': user_data[0][2].split(',')
    # }
    #     # print("user learning profile : ", learner_profile)
    #     learner_pref = get_user_membership(session.get("user_id")) #learner_pref {'Auditory': 0.31606664251378125, 'Kinesthetic': 0.3079119262012944, 'Read/Write': 0.062026319117999336, 'Visual': 0.313995112166925}
    #     # print("learner_pref", learner_pref)
    #     # print("videos: ", videos)
    #     # print("video[0]: ", videos[0])
    #     filterd_resources = filter_resources(learner_profile, videos)
    #     # print("filter resource: ", filterd_resources[:2])
    #     # print(len(filterd_resources))
    #     ranked_resources = []
    #     if(len(filterd_resources) != 0):
    #         ranked_resources = rank_resources(filterd_resources, learner_pref)
    #     else:
    #         ranked_resources = []
        # print("ranked_resources resources: ", ranked_resources[:2])
        return render_template('recommended.html', videos=ranked_resources)
    except Exception as e:
        print("exception in recommended page: ", e)
        return render_template('recommended.html', videos=[])


def sanitize_rating(rating):
  
    try:
        rating = float(rating)  # Attempt to convert to float
        if rating > 5:
            return 5
        elif rating < 0:
            return 0
        else:
            return math.ceil(rating) #ciel the value
    except (TypeError, ValueError):
        return 4

def is_youtube_url(url):
    
    if not url:
        return False

    try:
        parsed_url = urlparse(url)
        host = parsed_url.netloc.lower()
        path = parsed_url.path.lower()

      
        if host in ('www.youtube.com', 'youtube.com', 'm.youtube.com', 'youtu.be'):
            return True

        
        if host == 'www.youtube-nocookie.com' and '/embed/' in path:
            return True

        
        if host == 'youtube.com' and '/shorts/' in path:
            return True

       
        if host == 'www.youtube.com' and '/live/' in path:
            return True

        
        if host == 'music.youtube.com' :
            return True

       
        if host == 'studio.youtube.com':
            return True

        
        if host == 'www.youtubekids.com' or host == 'youtubekids.com':
          return True

        return False

    except ValueError:
        return False
    except Exception:
        return False

@resource_bp.route("/full_course_list", methods=["GET", "POST"])
def full_course_list():
    videos = []
    user_data = None
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, grade, stream, subject, module_name, subtopic, description, video_filename, file_filename, urlUpload1 as url, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual
        FROM videos
        ''')
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
    return render_template('full_course_list.html',videos=videos)

@resource_bp.route('/course_details/<int:video_index>', methods=['GET', 'POST'])
def course_details(video_index):
    # print("video_index", video_index)
    resource = None
    interaction_data = False
    user_id = session.get("user_id")
    print('user id in details page: ', user_id)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE id=?',
                    (video_index,))
        resource = cursor.fetchone()   
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
        cursor.execute('SELECT * FROM user_interactions WHERE user_id=? AND course_id=?', (user_id, video_index))
        interaction_data = cursor.fetchone()   
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    # print("resource data; ", resource)
    # print("interaction_data; ", interaction_data)
    if(interaction_data):
        return redirect(url_for('resource_route.learn',course_id=video_index))
    return render_template('course_details.html', resource=resource, interaction_data=interaction_data)

@resource_bp.route('/create_enrollment', methods=['POST'])
def create_enrollment():
    data = request.get_json() 
    if data and 'message' in data:
        message = data['message']
        print("message from enroll: ", message)  #message from enroll:  {'course_id': '1', 'user_id': '2'}
            # db entry in enrollments check if same user already have an enrollment for the same course
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_interactions (course_id, user_id, course_status) VALUES (?, ?, ?)
            ''', (message.get("course_id", 0), message.get('user_id'), 'enrolled'))
            
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)

        result = f"Flask received: {message}"
        return jsonify({'result': "ok"})
    else:
        return jsonify({'error': 'Invalid request'}), 400


@resource_bp.route("/my_courses", methods=["POST", "GET"])
def my_courses():
    user_id = session.get("user_id")
    videos = None
    conn = get_db_connection()
    # print("user id : ", user_id)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                ui.interaction_id,
                ui.course_id,
                ui.user_id,
                ui.enrollment_id,
                ui.lessonid,
                ui.course_status,
                ui.interaction_type,
                v.title,
                v.grade,
                v.stream,
                v.subject,
                v.module_name,
                v.subtopic,
                v.description,
                v.video_filename,
                v.file_filename,
                v.urlUpload1,
                u.username,
                u.email
            FROM  
                user_interactions ui
            JOIN
                videos v ON ui.course_id = v.id
            JOIN
                users u ON ui.user_id = u.id
            WHERE
                ui.user_id = ?
                AND ui.course_status <> 'completed'
        ''', (user_id,))
        videos = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    print("videos in my courses: ", videos)
    return render_template('my_courses.html', videos=videos)

# @resource_bp.route('/activity/<int:activity_id', method=['POST', "GET"])
# def activity(activity_id):
#     print("activity id: ", id)
#     return render_template('activity.html')


@resource_bp.route('/activity/<int:course_id>', methods=["POST", "GET"])
def actvity(course_id):
    activity_details = None
    conn = get_db_connection()
    print("couse id ", course_id)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exercise WHERE course_id=?
        ''', (course_id,))
        activity_details = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)    
    
    print("course deatils", activity_details)  
    return render_template('activity.html', activity_details=activity_details)  


@resource_bp.route('/learn/<int:course_id>', methods=["POST", "GET"])
def learn(course_id):
    course_details = None
    conn = get_db_connection()
    print("couse id ", course_id)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM videos WHERE id=?
        ''', (course_id,))
        course_details = cursor.fetchone()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    print("course deatils", course_details)
    is_youtube = is_youtube_url(course_details[8])
    # is_youtube = is_youtube_url("https://www.google.com")
    # print("is youtube: ", is_youtube)
    video_id = None
    if(is_youtube):
        match = re.search(r"embed/([a-zA-Z0-9_-]+)", course_details[8])

        if match:
            video_id = match.group(1)
            print("Video ID:", video_id)
        else:
            print("No video ID found")
    excersise = False
    if course_details[8] == 'activity':
        excersise = True
        print("excersise: ", excersise)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timespend FROM user_interactions WHERE course_id=? AND user_id=?
        ''', (course_id,session.get('user_id')))
        interaction_data = cursor.fetchone()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}") 
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    print("interaction on course: ", interaction_data)
    interaction_time = interaction_data[0]
    print("vide id: ", video_id)
        
    return render_template('learning_page.html', course_details=course_details, is_youtube=is_youtube, video_id=video_id, excersise=excersise, interaction_time=interaction_time)



@resource_bp.route('/record_interaction', methods=["POST", "GET"])
def record_interaction():
    data = request.get_json() 
    user_id = session.get("user_id")
    print("interaction data: ", data)
    print("user_id: ", user_id)
    conn = get_db_connection()
    print("connetion : ", conn)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_interactions
            SET 
                timespend = timespend + ?, 
                no_of_clicks = no_of_clicks + 1
            WHERE course_id = ? AND user_id = ?;
        ''', (data.get("time_spent")/1000,data.get("video_id"), user_id))
        # videos = cursor.fetchall()
        print("cursor : ", cursor)
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    return "True"




@resource_bp.route('/record_completion', methods=["POST", "GET"])
def record_completion():
    data = request.get_json() 
    user_id = session.get("user_id")
    video = None
    # print("interaction data: ", data)
    # print("user_id: ", user_id)
    conn = get_db_connection()
    print("user id : ", user_id)
    rating = sanitize_rating(data.get("rating"))

    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_interactions
            SET 
                course_status = ?,
                rating = ?
            WHERE course_id = ? AND user_id = ?;
        ''', (data.get("status"), rating, data.get("video_id"), user_id))
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
        print("video id in update: ", data.get("video_id"))
        cursor = conn.cursor()
        selected_video_id = int(data.get("video_id"))
        cursor.execute('SELECT auditory, kinesthetic, read_write, visual, accessibility1 FROM videos WHERE id = ?', (selected_video_id,)) 
    # video = cursor.fetchall()
        video = cursor.fetchall()
        print("video value from db: ", video)
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    print("video data to update: ", video)
    vid_voice_score = 0
    vid_transcript_score = 0
    vid_subtitle_score = 0
    vid_captions_score = 0
    vid_isl_only_score = 0
    vid_isl_and_voice_score = 0
    a = k = r = v = 0
    row = None
    if(video):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            a, k, r, v, acc = video[0]  
            acc = [a.strip() for a in acc.split(',')]
            print("a, k, r, v, acc: ", a, k, r, v, acc)
            

            if 'Voice only' in acc:
                vid_voice_score = 1.0
            if 'Transcripts' in acc:
                vid_transcript_score = 1
            if 'Subtitle' in acc:
                vid_subtitle_score = 1
            if 'Captions' in acc:
                vid_captions_score = 1
            if 'ISL only' in acc:
                vid_isl_only_score = 1
            if 'ISL and Voice' in acc:
                vid_isl_and_voice_score = 1

            cursor.execute("SELECT auditory, kinesthetic, read_write, visual, isl_score, voice_score, isl_voice_score, subtitle_score, caption_score, transcript_score FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            print("row: ", row)
            auditory = row[0] + a
            kinesthetic = row[1] + k
            read_write = row[2] + r
            visual = row[3] + v

            isl_score = row[4] + vid_isl_only_score
            voice_score = row[5] + vid_voice_score
            isl_voice_score = row[6] + vid_isl_and_voice_score
            subtitle_score = row[7] + vid_subtitle_score
            caption_score = row[8] + vid_captions_score
            transcript_score = row[9] + vid_transcript_score

          
            total_learn = auditory + kinesthetic + read_write + visual
            total_acc = isl_score + voice_score + isl_voice_score + subtitle_score + caption_score + transcript_score
            print("total_learn, total_acc: ", total_learn, total_acc)

          
            if total_learn > 0:
                auditory /= total_learn
                kinesthetic /= total_learn
                read_write /= total_learn
                visual /= total_learn

            if total_acc > 0:
                isl_score /= total_acc
                voice_score /= total_acc
                isl_voice_score /= total_acc
                subtitle_score /= total_acc
                caption_score /= total_acc
                transcript_score /= total_acc

            print("auditory, kinesthetic, read_write, visual: ", auditory, kinesthetic, read_write, visual)
            print("isl_score, voice_score, isl_voice_score, subtitle_score, caption_score, transcript_score: ", isl_score, voice_score, isl_voice_score, subtitle_score, caption_score, transcript_score)
            cursor.execute('''
                UPDATE users SET
                    auditory = ?, kinesthetic = ?, read_write = ?, visual = ?,
                    isl_score = ?, voice_score = ?, isl_voice_score = ?,
                    subtitle_score = ?, caption_score = ?, transcript_score = ?
                WHERE id = ?
            ''', (
                auditory, kinesthetic, read_write, visual,
                isl_score, voice_score, isl_voice_score,
                subtitle_score, caption_score, transcript_score,
                user_id
            ))
            # conn.commit()       
            # videos = cursor.fetchall()
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)

    return "True"





@resource_bp.route('/topic/<string:topic_name>', methods=["POST", "GET"])
def view_topic_course(topic_name):
    try:
        # print("topic name", topic_name)
        videos = []
        recommended_videos = []
        user_group_recommended_ids = []
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            search_words = [topic_name]
            placeholders = ' OR '.join(['LOWER(title) LIKE ?'] * len(search_words))
            search_patterns = ['%' + word.lower() + '%' for word in search_words]

            cursor.execute(f'''
                SELECT title, grade, stream, subject, module_name, subtopic, description, video_filename, file_filename, urlUpload1 as url, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, id
                FROM videos
                WHERE topic = ?
                            ''', (topic_name, ))
            videos = cursor.fetchall()
            print("total videos in topic", len(videos))
            conn.commit()
        except sqlitecloud.Error as e: 
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)
        # print("videos in topic: \n", videos)
        # print("\n\nlength of videos: ", len(videos))
        print("before profile ")
        recommended_videos = user_profile_recommendations(session.get("user_id"), videos)[:10]
        # print("recommended videos len: ", recommended_videos[0][0])
        # print(type(recommended_videos))
        # print(type(recommended_videos[0]))
        # print('\n')
        # print(len(recommended_videos[0]))  
        # print('\n')
        print("videso data : ", len(videos))
        # print('\n')
        # print(len(videos[0]))
        user_group_recommended_ids = get_data(session.get("user_id"), 25)
        print("user_group_recommended_ids: ", user_group_recommended_ids)
        # print('videos: ', videos[:3])
        user_group_recommended_videos = [video for video in videos if video[-1] in user_group_recommended_ids]
        print("user_group_recommended_videos: ", len(user_group_recommended_videos))
        # recommended_videos.append(user_group_recommended_videos)
        full_recommendation = user_group_recommended_videos + recommended_videos
        print("user group recommendations: ", full_recommendation)
        return render_template('topic.html', videos=videos, topic_name=topic_name, recommended_videos=full_recommendation)
    except Exception as e:
        print("exception in topic page: ", e)
        return render_template('topic.html', videos=[], topic_name=topic_name, recommended_videos=[])  




@resource_bp.route('/lesson/<string:lesson_name>', methods=["POST", "GET"])
def view_lesson_topics(lesson_name):
    try:
        print("topic name", lesson_name)
        topics = get_topic_list(lesson_name)
        print("topics: ", topics)
       
        # conn = get_db_connection()
        # try:
        #     cursor = conn.cursor()
            

        #     cursor.execute(f'''
        #         SELECT topic_name, description 
        #         FROM topic
        #         WHERE lesson = ?
        #                     ''', (lesson_name, ))
        #     topics = cursor.fetchall()
        #     conn.commit()
        # except sqlitecloud.Error as e:
        #     print(f"Database error: {e}")
        #     if conn:
        #         conn.rollback()
        # finally:
        #     if 'cursor' in locals() and cursor:  
        #         cursor.close()
        #     close_db_connection(conn)

        # print("topics in lesson: \n", topics)
        # # print("videos in topic: \n", videos)
        # print("\n\nlength of videos: ", len(videos))
        # recommended_videos = user_profile_recommendations(session.get("user_id"), videos)[:10]
        # print("recommended videos: ", len(recommended_videos))
        # user_group_recommended_ids = get_data(session.get("user_id"), 25)
        # print("user_group_recommended_ids: ", user_group_recommended_ids)
        # # print('videos: ', videos[:3])
        # user_group_recommended_videos = [video for video in videos if video[-1] in user_group_recommended_ids]
        # print("user_group_recommended_videos: ", len(user_group_recommended_videos))
        # # recommended_videos.append(user_group_recommended_videos)
        # user_group_recommended_videos.append(recommended_videos)
        return render_template('lesson.html', topics=topics, lesson_name=lesson_name)
    except Exception as e:
        print("exception in lesson page: ", e)
        return render_template('lesson.html', topics=[], lesson_name=lesson_name)  
    




def generate_vark_vector(primary_type, selected_features):

    BASE_MODALITY_MAPPING = {
        "Video":             [60, 30, 20, 80],  # auditory, kinesthetic, read_write, visual
        "Text":              [0, 10, 90, 10],
        "Interactive":       [20, 90, 40, 40],
        "Audio":             [80, 10, 20, 10],
        "Sign Language":     [0, 30, 30, 90]
    }

    FEATURE_ADJUSTMENT_MAPPING = {
        "Captions":          [0, 0, 20, 0],
        "Quiz/MCQs":              [0, 20, 20, 10],
        "Audio Narration":         [20, 0, 0, 0],
        "Animations":         [0, 10, 0, 15],
        "Interactive Simulation": [0, 30, 10, 10],
        "Visual/Images":            [0, 0, 0, 10],
        "Transcripts":       [0, 0, 30, 0]
    }
    
    vark_vector = [0, 0, 0, 0]
    total_max_score = 0 
    

    num_primary_types_found = 0
    for p_type in primary_type:
        if p_type in BASE_MODALITY_MAPPING:
            base_scores = BASE_MODALITY_MAPPING[p_type]
            for i in range(4):
                vark_vector[i] += base_scores[i]
            num_primary_types_found += 1
        else:
            print(f" Primary type '{p_type}' not found in BASE_MODALITY_MAPPING.")

    if num_primary_types_found == 0:
        print("No valid primary types found")
        return {}

  
    for feature in selected_features:
        if feature in FEATURE_ADJUSTMENT_MAPPING:
            adjustment_scores = FEATURE_ADJUSTMENT_MAPPING[feature]
            for i in range(4): 
                vark_vector[i] += adjustment_scores[i]
        else:
            print(f"Warning: Feature '{feature}' not found in FEATURE_ADJUSTMENT_MAPPING.")

    

    total_score_sum = sum(vark_vector)
    
    normalized_vark_scores = [0, 0, 0, 0]
    if total_score_sum > 0:
        for i in range(4):
            normalized_vark_scores[i] = (vark_vector[i] / total_score_sum) 
    else:
        normalized_vark_scores = [0, 0, 0, 0]


    
    vark_labels = ["auditory", "kinesthetic", "read_write", "visual"]
    final_vark_scores = {}
    for i, label in enumerate(vark_labels):
        final_vark_scores[label] = round(normalized_vark_scores[i], 2) 

    return final_vark_scores


@resource_bp.route('/create_resource', methods=["POST", "GET"])
def create_resource():
    if(request.method == 'POST'):
        title = request.form.get('title', '')
        grade = request.form.get('grade', '')
        stream = request.form.get('stream', '')
        subject = request.form.get('subject', '')
        moduleName = request.form.get('moduleName', '')
        topic = request.form.get('topic', '')
        subtopic = request.form.get('subtopic', '')
        description = request.form.get('description', '')
        urlUpload1 = request.form.get('urlUpload1', '')
        accessibility = ', '.join(request.form.getlist('accessibility1'))
        format = request.form.get('format', '')
        type = request.form.getlist('urltype')
        advanced_type = request.form.getlist('advanced_type')
        interactive_level = "" #request.form.get('interactive_level')
        difficulty_level = request.form.get('difficulty_level')
        deafness_suitability = request.form.getlist('deafness_suitability')
        communication_mode = request.form.getlist('communication_mode')
        estimated_time = request.form.get('time')

        learning_style_score = generate_vark_vector(type, advanced_type)
        print("learning_style_score: ", learning_style_score)
        auditory_score = learning_style_score.get('auditory', 0)
        kinesthetic_score = learning_style_score.get('kinesthetic', 0)
        read_write_score = learning_style_score.get('read_write', 0)
        visual_score = learning_style_score.get('visual', 0)
        conn = get_db_connection()
        last_video_id = None
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT  MAX(id)
                FROM videos
                            ''')
            last_video_id = cursor.fetchall()
            # print("total videos in topic", last_video_id)
            last_video_id = last_video_id[0][0] + 1 if last_video_id[0] is not None else 1
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
            

            cursor.execute(f'''
              INSERT INTO videos (id, title, grade, stream, subject, module_name, subtopic, description, urlUpload1, urltype, format, interactive_level, difficulty_level, accessibility1, video_filename, file_filename, created_at, updated_at, views, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, topic) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (last_video_id, title, grade, stream, subject, moduleName, subtopic, description, urlUpload1, type, format, interactive_level, difficulty_level, accessibility, "", "", "", "", "", deafness_suitability, communication_mode, auditory_score, kinesthetic_score, read_write_score, visual_score, topic))
            conn.commit()
        except sqlitecloud.Error as e: 
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)
        return render_template('create_resource.html', status=True) 

        # print('title: ', title)
        # print("grade", grade)
        # print("stream", stream)
        # print("subject", subject)
        # print("moduleName", moduleName)
        # print("topic ", topic)
        # print("subtopic", subtopic)
        # print("description",  description)
        # print("urlUpload1", urlUpload1)
        # print("accessibility",  accessibility)
        # print("format",  format)
        # print("urltype ", type)
        # print("interactive_level", interactive_level)  
        # print("difficulty_level", difficulty_level)
        # print("deafness_suitability ", deafness_suitability)
        # print("communication_mode", communication_mode)
        # print("advanced type: ", advanced_type)
        # print("estimated_time: ", estimated_time)




        # accessibility1 = ', '.join(request.form.getlist('accessibility1[]'))
        # cursor.execute('''
        #             INSERT INTO videos (id, title, grade, stream, subject, module_name, subtopic, description, urlUpload1, urltype, format, interactive_level, difficulty_level, accessibility1, video_filename, file_filename, created_at, updated_at, views, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, topic) 
        #                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        #         ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22], row[23], row[24], row[25]))
                
    return render_template('create_resource.html', status=False)  
