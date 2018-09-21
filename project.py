import rethinkdb as r



def table_creation(conn,db):
    r.db_create(db).run(conn)
    r.db(db).table_create('questions', primary_key='num').run(conn)
    r.db(db).table_create('clientpagestatus').run(conn)
    r.db(db).table('clientpagestatus').insert({'pageStatus':'hide'}).run(conn)
    r.db(db).table_create('team_details', primary_key='teamname').run(conn)
    r.db(db).table_create('team_answer', primary_key='question_num').run(conn)
