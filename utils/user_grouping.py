
import sqlitecloud
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

def get_db_connection():
   
    conn = sqlitecloud.connect('sqlitecloud://cqc1o5epnk.g1.sqlite.cloud:8860?apikey=HpND7AUzYbPU4EbIonwQG0vYys4XmfYSzCg6vjn3GOA')
    db_name = 'DLearnDB'
    conn.execute(f"USE DATABASE {db_name}")
    return conn

def close_db_connection(conn):
    if conn:
        conn.close()

def recommend_videos(user_similarity_df, user_item_matrix, user_id, top_n=5):
    if user_id not in user_similarity_df.index:
        return []

    similar_users = user_similarity_df[user_id].drop(user_id).sort_values(ascending=False).head(top_n)
    similar_users_ids = similar_users.index

    watched_videos = user_item_matrix.loc[user_id][user_item_matrix.loc[user_id] > 0].index
    recommendations = user_item_matrix.loc[similar_users_ids].mean().drop(watched_videos, errors='ignore')
    # print("recommendations", recommendations)
    return recommendations.sort_values(ascending=False).head(top_n)


def compute_style_match(user_profiles, row):
    user_id = row['user_id']
    user_vector = user_profiles.loc[user_id]
    video_vector = row[['auditory', 'kinesthetic', 'read_write', 'visual']]
    return cosine_similarity([user_vector], [video_vector])[0][0]

def get_data(user_id, top_n=5):
    interactions = []
    conn = get_db_connection()
    recommended_videos = None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ui.user_id, ui.course_id, ui.no_of_clicks, ui.timespend, ui.rating,
                       v.title as video_title, v.auditory, v.kinesthetic, v.read_write, v.visual
        FROM user_interactions ui JOIN videos v ON ui.course_id = v.id 
                       
        ''')
        interactions = cursor.fetchall()
        # print("interactions", interactions)
        conn.commit()
        if(len(interactions) > 0):
            df = pd.DataFrame(interactions, columns=[
        'user_id', 'video_id', 'clicks', 'time_spent', 'rating', 'video_title',
        'auditory', 'kinesthetic', 'read_write', 'visual'
    ])         
            df['rating'] = df['rating'].fillna(3)
            df['time_spent'] = df['time_spent'].fillna(10)
            df['clicks'] = df['clicks'].fillna(2)
            # print("df", df)
            user_profiles = df.groupby('user_id')[['auditory', 'kinesthetic', 'read_write', 'visual']].mean()
            # print("user_profiles", user_profiles)
            df['style_match'] = df.apply(lambda row: compute_style_match(user_profiles, row), axis=1)
            # print("df with style match", df)
            scaler = MinMaxScaler()
            df[['clicks_norm', 'time_spent_norm', 'rating_norm']] = scaler.fit_transform(
                df[['clicks', 'time_spent', 'rating']]
            )
            # print("df with normalized values", df)


            w_clicks = 0.2
            w_time = 0.2
            w_rating = 0.3
            w_style = 0.3
            df['total_score'] = (
                    w_clicks * df['clicks_norm'] +
                    w_time * df['time_spent_norm'] +
                    w_rating * df['rating_norm'] +
                    w_style * df['style_match']
                )
            # print("df with total score\n", df)
            user_item_matrix = df.pivot_table(index='user_id', columns='video_id', values='total_score').fillna(0)
            # print("user_item_matrix\n", user_item_matrix)
            user_similarity = cosine_similarity(user_item_matrix)
            # print("user_similarity\n", user_similarity)
            user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)
            # print("user_similarity_df\n", user_similarity_df)
            recommended_videos = recommend_videos(user_similarity_df, user_item_matrix, user_id, top_n)
        # print("recommended_videos ids\n", recommended_videos)
        
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        return []
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
        if recommended_videos is not None and len(recommended_videos) > 0:
            print("recommended videos inside user group filter: ", recommended_videos)
            return recommended_videos.index.tolist()
        return []

        




def test_function():
    conn = get_db_connection()
    interactions = None
    # recommended_videos = None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT course_id
        FROM user_interactions  
                       
        ''')
        interactions = cursor.fetchall()
        # print("interactions", interactions)
        conn.commit()
        
        
    except sqlitecloud.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        return []
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        close_db_connection(conn)
    print("interactions", list(set(interactions)))


if __name__ == "__main__":
    test_function()
    # get_data(5)