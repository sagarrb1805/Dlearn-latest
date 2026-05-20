from db.db import get_db_connection, close_db_connection
import sqlitecloud


class Common:
    model = None



def get_user_membership(user_id):
    if(user_id):
        user_learning_preference = None
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT learning_style
            FROM learning_content_preference WHERE id = ?
            ''', (user_id,))
            user_learning_preference = cursor.fetchall()
            # print("user_learning_preference : ", user_learning_preference)
            conn.commit()
        except sqlitecloud.Error as e:
            print(f"Database error: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            close_db_connection(conn)

        user_learning_preference = user_learning_preference[0][0].split(",")
        user_learning_preference = [item.lower() for item in user_learning_preference]

        # print(user_learning_preference, type(user_learning_preference))
        preference_array = []
        if("aural" in user_learning_preference):
            preference_array.append(1)
        else:
            preference_array.append(0)
        if("kinesthetic" in user_learning_preference):
            preference_array.append(1)
        else:
            preference_array.append(0)
        if("read/write" in user_learning_preference):
            preference_array.append(1)
        else:
            preference_array.append(0)
        if("visual" in user_learning_preference):
            preference_array.append(1)
        else:
            preference_array.append(0)
        # print(preference_array)
        user_result = Common.model.get_learner_membership(user_features=preference_array)
        # print("user result: ", user_result)
        cluster_feature_score = user_result['Cluster Feature Scores']
        print("\ncluster feature score: ", cluster_feature_score)
        total_weight = sum(cluster_feature_score.values())
        normalized_prefs = {key: val / total_weight for key, val in cluster_feature_score.items()}
        
        # print('\nleaner prefs; ', normalized_prefs)

        learner_prefs = {key: float(value) for key, value in normalized_prefs.items()}

        return learner_prefs
        # print("type of learning preference: ", type(user_learning_preference[0][0]))




    