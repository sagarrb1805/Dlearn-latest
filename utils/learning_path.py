import sqlitecloud
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from collections import Counter
from itertools import islice, groupby

def get_db_connection():
   
    conn = sqlitecloud.connect('sqlitecloud://cqc1o5epnk.g1.sqlite.cloud:8860?apikey=HpND7AUzYbPU4EbIonwQG0vYys4XmfYSzCg6vjn3GOA')
    db_name = 'DLearnDB'
    conn.execute(f"USE DATABASE {db_name}")
    return conn

def close_db_connection(conn):
    if conn:
        conn.close()

def get_ngrams(topic_list, n=2):
    return list(zip(*(islice(topic_list, i, None) for i in range(n))))



def get_user_learning_path():
    data = None
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT i.user_id, i.course_id, i.interaction_id, i.course_status, i.no_of_clicks,
       v.title, v.topic
FROM user_interactions AS i
JOIN videos AS v ON i.course_id = v.id
ORDER BY i.user_id, i.interaction_id
        """
#         cursor.execute("""
#             SELECT i.user_id, i.video_id, i.interaction_id, i.course_status, i.time_spent, i.click_count,
#        v.title, v.grade, v.subject, v.module_name, v.subtopic
# FROM user_interactions AS i
# JOIN videos AS v ON i.video_id = v.video_id
# ORDER BY i.user_id, i.interaction_id
#         """)
        merged = pd.read_sql_query(query, conn)
        # data = cursor.fetchall()
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
    # print("merged : ", merged)
    merged = merged[merged["topic"].notnull()]
    learning_paths = merged.groupby("user_id")["topic"].apply(list).reset_index()
    # print("learning_paths : \n", learning_paths)
    transactions = learning_paths["topic"].tolist()
    all_ngrams = []
    for path in transactions:  
        path = [t for t in path if t is not None]
        path = [key for key, _ in groupby(path)]
        if len(path) >= 2:
            all_ngrams.extend(get_ngrams(path, n=3))  

    ngram_counter = Counter(all_ngrams)
    most_common_patterns = ngram_counter.most_common(10)

    # Print top patterns
    print("\nTop existing learning patterns (bigrams):")
    for pattern, count in most_common_patterns:
        print(f"{pattern} → {count} learners")
    # te = TransactionEncoder()
    # te_ary = te.fit(transactions).transform(transactions)
    # df = pd.DataFrame(te_ary, columns=te.columns_)
    # frequent_patterns = apriori(df, min_support=0.2, use_colnames=True)
    # print("frequent_patterns : \n", frequent_patterns)
    # print("frequent_patterns : \n",frequent_patterns.sort_values(by="support", ascending=False))


if __name__ == "__main__":
    get_user_learning_path()