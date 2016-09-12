# import Flask
from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'ThisIsSecret!'
mysql = MySQLConnector(app,'the_wall')

@app.route('/', methods=['GET'])
def index():
	return render_template('index.html')

@app.route('/wall', methods=['GET'])
def wall():
	user_query = 'SELECT * FROM users WHERE id = :id LIMIT 1'
	query_data = { 'id': session['id'] }
	user = mysql.query_db(user_query, query_data)
	first_name = user[0]['first_name']

	message_query = 'SELECT messages.message, messages.id AS message_id, messages.created_at AS message_created, users.first_name, users.last_name FROM messages LEFT JOIN users on users.id = messages.user_id ORDER BY message_created DESC'
	messages = mysql.query_db(message_query)

	comment_query = 'SELECT comments.comment, comments.message_id, comments.created_at AS comment_created, users.first_name, users.last_name FROM comments LEFT JOIN users on users.id = comments.user_id ORDER BY comment_created' 
	comments = mysql.query_db(comment_query)

	return render_template('wall.html', first_name=first_name,messages=messages,comments=comments)  

@app.route('/logout', methods=['POST'])
def logout():
	session.pop('id', None)
	flash('You were logged out!')
	return redirect('/')

@app.route('/message', methods=['POST'])
def message():
	message = request.form['message'] 	
	query = 'INSERT INTO messages SET message = :message, user_id = :user_id, created_at = NOW(), updated_at = NOW()'
	data = {
		'message': request.form['message'], 
		'user_id': session['id']
	}
	mysql.query_db(query, data)
	return redirect('/wall')

@app.route('/comment/<message_id>', methods=['POST'])
def comment(message_id):
	comment = request.form['comment']	
	query = 'INSERT INTO comments SET user_id = :user_id, message_id = :message_id, comment = :comment, created_at = NOW(), updated_at = NOW()'
	data = {
		'message_id': message_id,
		'comment': comment, 
		'user_id': session['id']
	}
	mysql.query_db(query, data)
	return redirect('/wall')	

@app.route('/delete/<message_id>', methods=['POST'])
def delete(message_id):
	comment_query = 'DELETE FROM comments WHERE message_id = :message_id'
	query_data = { 'message_id': message_id }
	mysql.query_db(comment_query, query_data)

	message_query = 'DELETE FROM messages WHERE id = :message_id'
	mysql.query_db(message_query, query_data)

	return redirect('/wall')

@app.route('/login', methods=['POST'])
def login():  
	email_address = request.form['email_address']
	password = request.form['password']

	user_query = 'SELECT * FROM users WHERE email_address = :email_address LIMIT 1'
	query_data = { 'email_address': email_address }
	user = mysql.query_db(user_query, query_data) # user will be returned in a list
	if user == []:
		flash('You entered an invalid email! Try again!')
		return redirect('/')
	else:	
		if bcrypt.check_password_hash(user[0]['pw_hash'], password):
			session['id'] = user[0]['id']
			return redirect('/wall')
		else:
			flash('Invalid password!')
			return redirect('/')			

@app.route('/registration', methods=['POST'])
def registration():

	first_name = request.form['first_name']
	last_name = request.form['last_name']
	email_address = request.form['email_address']
	password = request.form['password']
	confirm_password = request.form['confirm_password']
	email_regex = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
	name_match = r'^[a-zA-Z]+$'
	pass_require = r'(?=.*[A-Z]+)(?=.*[0-9]+)'
	errors = False

	if len(first_name) < 1:
		flash('First name cannot be blank!')
		errors = True
	else:	
		if len(first_name) < 2:
			flash('First name must have at least 2 characters!')	
			errors = True
		if not re.search(name_match, first_name):
			flash('First name can only contain letters!')	
			errors = True
	if len(last_name) < 1:
		flash('Last name cannot be blank!')
		errors = True
	else:	
		if len(last_name) < 2:
			flash('Last name must have at least 2 characters!')	
			errors = True
		if not re.search(name_match, last_name):
			flash('Last name can only contain letters!')
			errors = True
	if len(email_address) < 1:
		flash('Email cannot be blank!')
		errors = True
	elif not email_regex.match(email_address):
		flash('Invalid email address!') 		 	
		errors = True
	else:
		user_query = 'SELECT * FROM users WHERE email_address = :email_address'
		query_data = { 'email_address': email_address }
		user = mysql.query_db(user_query, query_data) # user will be returned in a list
		if user != []:
			flash('User already exists! Please try another email address!')	
			errors = True
	if len(password) < 1:
		flash('Password cannot be blank! Password must be at least 8 characters and contain at least 1 capital letter and 1 number!')
		errors = True
	else:	
		if len(password) < 8:
			flash('Password cannot be less than 8 characters!')
			errors = True
		if not re.search(pass_require, password):
			flash('Password must contain at least 1 capital letter and 1 number!')
			errors = True
	if len(confirm_password) < 1:
		flash('Confirm password cannot be blank!')
		errors = True	
	if confirm_password != password:
		flash('Confirm password and password must match!')
		errors = True
	
	print errors

	if errors == True:
		return redirect('/')

	if errors == False:
		flash('Success!')
		pw_hash = bcrypt.generate_password_hash(request.form['password'])
		query = 'INSERT INTO users SET first_name = :first_name, last_name = :last_name, email_address = :email_address, pw_hash = :pw_hash, created_at = NOW(), updated_at = NOW()'
		data = {
		         'first_name': first_name, 
		         'last_name':  last_name,
		         'email_address': email_address,
		         'pw_hash': pw_hash
		       }
		mysql.query_db(query, data)
		return redirect('/')

app.run(debug=True)
