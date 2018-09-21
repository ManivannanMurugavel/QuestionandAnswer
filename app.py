from flask import Flask, render_template, Response, request, jsonify, make_response
import time
import rethinkdb as r
import json
import project as pj



conn = r.connect(host='localhost',
			 port=28015)
db = "None"
auth = False
projectname = "None"
username = ""
addUser = True
currQuesNum = 0;
teamAnswer = []

app = Flask(__name__)
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/question')
def question():
	return render_template('question.html')


@app.route('/put_question')
def put_question():
    print("sdc")
    username = request.args['name']
    question = request.args['question']
    print(username,question)
    r.connect( "localhost", 28015).repl()
    r.db("whirldata").table("questions").insert([{'name':username,'question':question}]).run()
    return "success"

@app.route('/uploadQuestion',methods=["POST","GET"])
def uploadQuestion():
	global projectname
	print("uploadQuestion")
	num = 1
	if(request.method == "POST"):
		print(request.form)
		question_num = request.form['question_num']
		question_text = request.form['question_text']
		a = request.form['answer_a']
		b = request.form['answer_b']
		c = request.form['answer_c']
		d = request.form['answer_d']
		ans = request.form['correct_answer']
		num = int(question_num)+1
		conn.reconnect(noreply_wait=False)
		r.db(db).table("questions").insert({"num":question_num,"question":question_text,"a":a,"b":b,"c":c,"d":d,"ans":ans}).run(conn)
		conn.close()
	data = {'question_number':num,'projectname':projectname}
	return render_template('uploadQuestion.html',data = data)

@app.route('/admin')
def admin():
	return render_template('admin.html')

@app.route('/login')
def login():
	global auth
	global username
	username = request.args['username']
	password = request.args['password']
	print(username,password)
	conn.reconnect(noreply_wait=False)
	datas = r.db('user').table("user_details").filter({'username':username,'password':password}).run(conn)
	conn.close()
	status = len(list(datas))
	if(status > 0):
		auth = True
		print(auth)
		return "success"
	return "error"

@app.route('/project')
def project():
	if not auth:
		return render_template('try_again.html')
	projects = []
	conn.reconnect(noreply_wait=False)
	databases = r.db_list().run(conn)
	conn.close()
	print(list(databases))
	for database in list(databases):
		if(database.startswith(username) and username != ""):
			print(database)
			projects.append({'project':database.split('_')[1]})
	print(projects)
	return render_template('project.html',projects=projects)

#Create Project Service
@app.route('/create_project')
def create_project():
	global projectname
	global db
	projectname = request.args['projectname']
	print(username,projectname)
	db = "{}_{}".format(username,projectname)
	print(db)
	conn.reconnect(noreply_wait=False)
	pj.table_creation(conn,db)
	conn.close()
	return "success"

#Select Project Service
@app.route('/select_project')
def select_project():
	global projectname
	global db
	projectname = request.args['projectname']
	print(username,projectname)
	db = "{}_{}".format(username,projectname)
	print(db)
	conn.reconnect(noreply_wait=False)
	dbs = r.db_list().run(conn)
	r.db(db).table('team_details').delete().run(conn)
	conn.close()
	if db in list(dbs):
		return "success"
	return "failed"

@app.route('/project_questions')
def project_questions():
	if db == "None":
		return render_template('try_again.html')
	conn.reconnect(noreply_wait=False)
	questions = r.db(db).table('questions').order_by('num').run(conn)
	conn.close()
	questions = list(questions)
	print(questions)
	return render_template('project_questions.html',projectname=projectname,questions=questions)

@app.route('/teams')
def teams():
	conn.reconnect(noreply_wait=False)
	teams = r.db(db).table('team_details').run(conn)
	conn.close()
	# print(list(teams))
	teams = list(teams)
	print(len(teams))
	return render_template('teams.html',teams=teams)

@app.route('/create_team')
def create_team():
	teamName = request.args['teamName']
	conn.reconnect(noreply_wait=False)
	r.db(db).table("team_details").insert({'teamName':teamName}).run(conn)
	conn.close()
	return "success"

@app.route('/quiz')
def quiz():
	try:
		conn.reconnect(noreply_wait=False)
		datas = r.db(db).table('clientpagestatus').run(conn)
		divstatus = list(datas)[0]['pageStatus']
		conn.close()
		print(divstatus)
		return render_template('quiz.html',divstatus=divstatus)
	except:
		return render_template('refresh.html')

@app.route('/server',methods=['GET','POST'])
def server():
	global currQuesNum
	global teamAnswer
	global auth
	print(auth)
	if not auth:
		return render_template('try_again.html')
    # r.connect( "localhost", 28015).repl()
	num = 1
	teamAnswer = []
	if(request.method == "POST"):
		print("POST")
		print(request.form)
		num = int(request.form['question_num'])
		num += 1
	currQuesNum = num
	conn.reconnect(noreply_wait=False)
	datas = r.db(db).table("questions").filter({'num':str(num)}).run(conn)
	divstatus = list(r.db(db).table('clientpagestatus').run(conn))[0]['pageStatus']
	conn.close()
	datas = list(datas)
	datas[0]['divstatus'] = divstatus
	print(datas[0])
	return render_template('server.html',data=datas[0])

@app.route('/save_answer')
def save_answer():
	global teamAnswer
	print(request.args)
	teamName = request.args['teamName']
	ans = request.args['ans']
	teamAnswer.append({'teamName':teamName,'ans':ans})
	print(currQuesNum)
	return "success"

@app.route('/get_answer')
def get_answer():
	# teamAnswer = [{'ans': 'd', 'teamName': 'Jarvis'}]
	print(teamAnswer)
	return jsonify(teamAnswer)

@app.route('/clientstatus')
def clientstatus():
	status = request.args['status']
	print(status)
	conn.reconnect(noreply_wait=False)
	if(status == "true"):
		print("true")
		r.db(db).table('clientpagestatus').update({"pageStatus":"show"}).run(conn)
	else:
		print("false")
		r.db(db).table('clientpagestatus').update({"pageStatus":"hide"}).run(conn)
		print('Question Num is {} and Length is {}'.format(currQuesNum,len(teamAnswer)))
	conn.close()
	return "success";
@app.route('/team_name')
def team_name():
	return "success"

@app.route('/divstatus')
def divstatus():
	print("Streaming")
	def divstatusstream():
		r.connect( "localhost", 28015).repl()
		try:
			cursor = r.db(db).table("clientpagestatus").changes().run()
			for document in cursor:
				print(document)
				yield "data:" + str(document['new_val']['pageStatus']) + "\n\n"
		except:
			pass
	return Response(response = divstatusstream(),status=200, mimetype= 'text/event-stream')

@app.route('/progress')
def progress():
	print("Streaming")
	def generate():
		try:
			r.connect( "localhost", 28015).repl()
			# print(db)
			cursor = r.db(db).table("questions").changes().run()
			for document in cursor:
				# yield ret
				yield "data:" + str(document['new_val']).replace("'",'"') + "\n\n"
		except:
			pass

	return Response(response = generate(),status=200, mimetype= 'text/event-stream')

@app.route('/team_status')
def team_status():
	print('team stream')
	def team_stream():
		try:
			r.connect( "localhost", 28015).repl()
			cursor = r.db(db).table("team_details").changes().run()
			for document in cursor:
				print(document)
				yield "data:" + str(document['new_val']['teamName']).replace("'",'"') + "\n\n"

		except:
			pass

	return Response(response = team_stream(),status=200, mimetype= 'text/event-stream')



if __name__ == "__main__":
	app.run(host="0.0.0.0",debug=True)
