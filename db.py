#db.py

import sqlite3
import csv

""" Building database of the CSV files with the repective table names """

NODES_PATH = "bburg_nodes.csv"
NODE_TAGS_PATH = "bburg_nodes_tags.csv"
WAYS_PATH = "bburg_ways.csv"
WAY_NODES_PATH = "bburg_ways_nodes.csv"
WAY_TAGS_PATH = "bburg_ways_tags.csv"

DB_filename = 'bburg_map.db'

def to_database():

    sqlite_file = DB_filename # if the file name doesn't exist, create it
    conn = sqlite3.connect(sqlite_file) # connect to the db
    cur = conn.cursor() # get a cursor object

    # drop the table if it is already exists
    cur.execute('''DROP TABLE IF EXISTS nodes''')
    conn.commit()

    # create 'nodes' table, specifying the column names and data types
    cur.execute('''
    CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
    );''')

    # read csv file as a dictionary, and format the data as a list of tuples
    with open(NODES_PATH,'rb') as fin:
        dr = csv.DictReader(fin) 
        to_db = [(i['id'].decode("utf-8"), i['lat'].decode("utf-8"), i['lon'].decode("utf-8"), \
                i['user'].decode("utf-8"), i['uid'].decode("utf-8"), i['version'].decode("utf-8"), \
                i['changeset'].decode("utf-8"), i['timestamp'].decode("utf-8")) \
                for i in dr]

        # insert the formatted data
    cur.executemany("INSERT INTO nodes (id, lat, lon, user, uid, version, changeset, timestamp) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    conn.commit()

    #create nodes_tags table
    cur.execute('''
    CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
    );''')
    with open(NODE_TAGS_PATH,'rb') as fin:
        dr = csv.DictReader(fin) 
        to_db = [(i['id'].decode("utf-8"), i['key'].decode("utf-8"), i['value'].decode("utf-8"), \
                i['type'].decode("utf-8")) for i in dr]

    cur.executemany("INSERT INTO nodes_tags (id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
    conn.commit()


    #Create ways table
    cur.execute('''
    CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
    );''')
    with open(WAYS_PATH,'rb') as fin:
        dr = csv.DictReader(fin) 
        to_db = [(i['id'].decode("utf-8"), i['user'].decode("utf-8"), i['uid'].decode("utf-8"), \
                i['version'].decode("utf-8"), i['changeset'].decode("utf-8"), \
                i['timestamp'].decode("utf-8")) for i in dr]

    cur.executemany("INSERT INTO ways (id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db)
    conn.commit()


    #Create ways_nodes table
    cur.execute('''
    CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
    );''')
    with open(WAY_NODES_PATH,'rb') as fin:
        dr = csv.DictReader(fin) 
        to_db = [(i['id'].decode("utf-8"), i['node_id'].decode("utf-8"), i['position'].decode("utf-8")) \
                for i in dr]

    cur.executemany("INSERT INTO ways_nodes (id, node_id, position) VALUES (?, ?, ?);", to_db)
    conn.commit()


    #Create ways_tags table
    cur.execute("""
    CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
    );""")
    with open(WAY_TAGS_PATH,'rb') as fin:
        dr = csv.DictReader(fin) 
        to_db = [(i['id'].decode("utf-8"), i['key'].decode("utf-8"), i['value'].decode("utf-8"), \
                i['type'].decode("utf-8")) for i in dr]

    cur.executemany("INSERT INTO ways_tags (id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
    conn.commit()


    conn.close() # close the connection

if __name__ == '__main__':
    to_database()