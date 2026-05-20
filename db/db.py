# import sqlitecloud


# conn = sqlitecloud.connect('sqlitecloud://cqc1o5epnk.g1.sqlite.cloud:8860?apikey=HpND7AUzYbPU4EbIonwQG0vYys4XmfYSzCg6vjn3GOA')

# db_name = 'DLearnDB'

# conn.execute(f"USE DATABASE {db_name}")
import sqlitecloud

def get_db_connection():
   
    conn = sqlitecloud.connect('sqlitecloud://cqc1o5epnk.g1.sqlite.cloud:8860?apikey=HpND7AUzYbPU4EbIonwQG0vYys4XmfYSzCg6vjn3GOA')
    db_name = 'DLearnDB'
    conn.execute(f"USE DATABASE {db_name}")
    return conn

def close_db_connection(conn):
    if conn:
        conn.close()
# db_query = "SELECT albums.AlbumId as id, albums.Title as title, artists.name as artist FROM albums INNER JOIN artists WHERE artists.ArtistId = albums.ArtistId LIMIT 20"


# cursor = conn.execute(db_query)
# print(cursor.fetchall())
# conn.close()