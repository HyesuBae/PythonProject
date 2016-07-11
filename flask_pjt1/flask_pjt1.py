# -*- coding: utf-8 -*-

from flask import Flask,url_for, request, render_template, make_response

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<h1>Hello World!</h1>"


@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(error)
    return render_template('page_not_found.html'), 404


@app.route("/hello/")
@app.route("/hello/<name>")
def hello(name=None):
    return render_template('hello.html', name=name)


@app.route("/hello_flask")
def hello_flask():
    return "Hello Flask world!"


@app.route("/<username>")
def hello_user(username):
    return "Hello "+username+"!"


@app.route("/<int:number>")
def get_number(number):
    return "You typed '%d'." % number


def index():
    response = make_response(render_template('index.html', foo=42))
    response.headers['X-Parachutes'] = 'parachutes are cool'
    return response




@app.route('/profile/', methods=['POST','GET'])
def profile(username=None):
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        #if not username and not email:
        #    return add_profile(request.form)
    #elif request.method == 'GET':
    #    username = request.args.get['username']
    #    email = request.args.get['email']
    else:
        error = 'Invalid username or email'


    return render_template('profile.html', error=error)



if __name__ == "__main__":
    with app.test_request_context():
        print url_for('hello')
        print url_for('hello_user', username='hyesu')

    #app.run(host='0.0.0.0', debug=True)
    app.run(debug=True)