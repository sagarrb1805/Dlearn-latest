from flask import Blueprint
from routes.resource_route import user_profile_recommendations
from db.db import get_db_connection, close_db_connection
import sqlitecloud
from utils.common import Common, get_user_membership
import pandas as pd
import numpy as np

from utils.recommendation import FuzzyClustering, filter_resources

test_bp = Blueprint('test', __name__)



def rank_resources(filtered_resources, learner_prefs):
    if not isinstance(learner_prefs, dict):
        raise ValueError("learner_prefs must be a dictionary with learning style scores.")

    
    columns = [
        'Title', 'Grade', 'Stream', 'Subject', 'ModuleName', 'Subtopic', 'Description',
        'VideoFilename', 'FileFilename', 'URL', 'ResourceID',
        'Accessibility', 'DeafnessSuitability', 'CommunicationMode',
        'Auditory', 'Kinesthetic', 'Read/Write', 'Visual', 'id'
    ]

   
    if not isinstance(filtered_resources, list) or not all(isinstance(item, tuple) for item in filtered_resources):
        raise ValueError("filtered_resources must be a list of tuples.")

    
    try:
        resources_dict_list = [dict(zip(columns, resource)) for resource in filtered_resources]
    except Exception as e:
        raise ValueError(f"Error in converting tuples to dictionary: {e}")

   
    resources_df = pd.DataFrame(resources_dict_list)

    
    numeric_cols = ['Auditory', 'Kinesthetic', 'Read/Write', 'Visual']
    for col in numeric_cols:
        resources_df[col] = pd.to_numeric(resources_df[col], errors='coerce')

    
    def calculate_score(row):
        try:
            weights = np.array([
                learner_prefs['Auditory'],
                learner_prefs['Kinesthetic'],
                learner_prefs['Read/Write'],
                learner_prefs['Visual']
            ])
            resource_values = np.array([
                row['Auditory'],
                row['Kinesthetic'],
                row['Read/Write'],
                row['Visual']
            ])
            # print("calculating weighted sum")
            # return np.dot(weights, resource_values)  # Weighted sum
        

            if np.linalg.norm(weights) == 0 or np.linalg.norm(resource_values) == 0:
                return 0  
            
            cosine_similarity = np.dot(weights, resource_values) / (np.linalg.norm(weights) * np.linalg.norm(resource_values))
            return cosine_similarity    
        except KeyError as e:
            raise ValueError(f"Missing key in learner_prefs: {e}")

    
    resources_df['Score'] = resources_df.apply(calculate_score, axis=1)
    
    # ranked_resources = resources_df.sort_values(by="Score", ascending=False)
    resources_df = resources_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    top_resources = resources_df.iloc[:7]
    remaining = resources_df.iloc[7:].copy()

    samples = []

    if not remaining.empty:
        def dominant_style(row):
            factors = {
                'Auditory': row['Auditory'],
                'Kinesthetic': row['Kinesthetic'],
                'Read/Write': row['Read/Write'],
                'Visual': row['Visual']
            }
            return max(factors, key=factors.get)

        remaining['Bucket'] = remaining.apply(dominant_style, axis=1)
        bucket_scores = remaining.groupby('Bucket')['Score'].mean().sort_values(ascending=False)

        max_sample = 5  
        bucket_sample_counts = {}
        total_buckets = len(bucket_scores)
        for rank, (bucket, avg_score) in enumerate(bucket_scores.items(), start=1):
            sample_size = max(1, max_sample - (rank - 1))  
            bucket_sample_counts[bucket] = sample_size

        for bucket, count in bucket_sample_counts.items():
            group = remaining[remaining['Bucket'] == bucket]
            sampled_group = group.nlargest(count, 'Score')
            samples.append(sampled_group)

    if samples:
        bucketed_resources = pd.concat(samples)
        final_recommendations = pd.concat([top_resources, bucketed_resources])
    else:
        final_recommendations = top_resources

    # final_recommendations = pd.concat([top_resources, bucketed_resources]).sort_values(by="Score", ascending=False).reset_index(drop=True)

    # print("Ranked Resources: ", ranked_resources)
    final_recommendations = final_recommendations.sort_values(by="Score", ascending=False).reset_index(drop=True)
   
    # ranked_resources_list = [tuple(row) for row in final_recommendations.itertuples(index=False, name=None)]
    for col in ['Accessibility', 'DeafnessSuitability', 'CommunicationMode']:
        # Ensure the column exists and handle potential non-list values gracefully
        if col in final_recommendations.columns:
            final_recommendations[col] = final_recommendations[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )
            # Handle potential None/NaN values explicitly if they might appear
            final_recommendations[col] = final_recommendations[col].fillna('')



    original_columns = [
        'Title', 'Grade', 'Stream', 'Subject', 'ModuleName', 'Subtopic', 'Description',
        'VideoFilename', 'FileFilename', 'URL', 'ResourceID',
        'Accessibility', 'DeafnessSuitability', 'CommunicationMode',
        'Auditory', 'Kinesthetic', 'Read/Write', 'Visual', 'id'
    ]

    # Select only the original columns from the final_recommendations DataFrame
    # This creates a new DataFrame with only the desired columns
    filtered_output_df = final_recommendations[original_columns]

    # Convert this filtered DataFrame to a list of tuples
    ranked_resources_list = [tuple(row) for row in filtered_output_df.itertuples(index=False, name=None)]
    
    return ranked_resources_list
    
    return ranked_resources_list



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

def profile_recommendations(user_id, videos=[]):
    try:
        videos = videos
        user_data = None
        if user_id is None:
            return []
        

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
        if(user_interaction_count < 3):
            return False
            learner_pref = get_user_membership(user_id) #learner_pref {'Auditory': 0.31606664251378125, 'Kinesthetic': 0.3079119262012944, 'Read/Write': 0.062026319117999336, 'Visual': 0.313995112166925}
        else:
            conn = get_db_connection()   
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                    auditory, kinesthetic, read_write, visual
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
        # print("learner_pref: ", learner_pref)
        # user_interaction_count = get_user_preference(user_id)
        # print("videos: ", videos)
        # print("video[0]: ", videos[0])
        filterd_resources = filter_resources(learner_profile, videos)
        print("filter resourcellength: ")
        print(len(filterd_resources))
        ranked_resources = []
        if(len(filterd_resources) != 0):
            ranked_resources = rank_resources(filterd_resources, learner_pref)
        else:
            ranked_resources = []
        print("ranked_resources resources: ", ranked_resources[:2])
        print("len of ranged resource fields: ", len(list(ranked_resources[0])))
        return ranked_resources
    except Exception as e:
        print("exception in user profile recommended page: ", e)
        return []
 

@test_bp.route('/get_inetraction_data_list', methods=['GET'])
def get_interaction_data_list():
    interaction = None
    response = {}
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT user_id, course_id
            FROM user_interactions'''
            )
        interaction = cursor.fetchall()
        conn.commit()
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)

    for interaction_data in interaction:
        # print("interaction_data : ", interaction_data)
        user_id = interaction_data[0]
        course_id = interaction_data[1]
        if user_id not in response:
            response[user_id] = []
        response[user_id].append(course_id)
        # print("user id : ", user_id)
        # print("course id : ", course_id)
        #
    print("interaction : ", interaction[:])
        # break
    print("response : ", response)

    return response

@test_bp.route('/get_data', methods=['GET'])
def get_test_data():
    return {'message': "hello world"}


@test_bp.route('/get_recommendations_list', methods=['GET'])
def get_recommendations_list():
    users = None
    response = {}
    videos = None
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT title, grade, stream, subject, module_name, subtopic, description, video_filename, file_filename, urlUpload1 as url, id, accessibility1 as accessibility, deafness_suitability, communication_mode, auditory, kinesthetic, read_write, visual, id
            FROM videos'''
            )
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


    conn = get_db_connection()   
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
            id FROM users
        ''')
        users = cursor.fetchall()
        # count = count[0][0]
        # print("users : ", users)
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
    

    for user in users:
        # print("user id : ", user[0])
        # if(user[0] == 53):
        user_recommendations = profile_recommendations(user[0], videos)
        print("user recommendations: ", user_recommendations)
        id_list = []
        if(user_recommendations != False):
            for recommendation in user_recommendations:
                id_list.append(recommendation[-1])
                
            # print("user_recommendations : ", user_recommendations)
            # print("id_list : ", id_list)     
            response[user[0]] = id_list
        # break
    print("response : ", response)

    return response