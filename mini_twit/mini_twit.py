# -*- coding: utf-8 -*-

import time
from datetime import datetime
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, g, session, url_for, redirect, request, flash, render_template, abort
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
from hashlib import md5

# Configuration
DATABASE = '/home/hyesubae/PycharmProjects/mini_twit/mini_twit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'my secret key :)'


# Create application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('MINI_TWIT_SETTINGS', silent=True)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())

        db.commit()


# one : 결과값으로 리스트 전체를 받을 것인지 리스트의 첫번째 요소만 받을 것인지 결정하는 boolean 값
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)

    # cursor에서 전체 레코드를 fetch하여 row를 한 줄씩 읽으면서 그 row에 있는 column의 이름과 값을 dict 형태로 변환.
    rv = [dict((cur.description[idx][0], value) for idx, value in enumerate(row))
          for row in cur.fetchall()]

    # one이 True이면 한 개의 row만 리턴, False이면 전체 row 리턴
    return (rv[0] if rv else None) if one else rv


# 각 요청에 앞서서 실행되는 함수
@app.before_request
def before_request():
    # g : global 객체. 한 번의 요청에 대해서만 같은 값을 유지하며 스레드에 안전하다.
    g.db = connect_db()
    g.user = None

    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?', [session['user_id']], one=True)


# 각 응답이 생성된 후에 실행되는 함수
# @app.after_request는 예외가 발생하면 실행되지 않음
@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def get_user_id(username):
    rv = g.db.execute('select user_id from user where username = ?',
                      [username]).fetchone()
    return rv[0] if rv else None


# view 함수 구현
@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('timeline'))

    error = None

    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif get_user_id(request.form['username']):
            error = 'The username is already taken'
        else:
            g.db.execute('insert into user(username, email, pw_hash) values(?, ?, ?)',
                         [request.form['username'],
                          request.form['email'],
                          generate_password_hash(request.form['password'])])
            g.db.commit()
            # flash : view 함수에서 정의한 메지리르 템플릿에서 사용하기 위한 메커니즘.
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET','POST'])
def login():
    if g.user:
        return redirect(url_for('timeline'))

    error = None

    if request.method == 'POST':
        user = query_db('select * from user where username= ?',[request.form['username']], one=True)

        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'], request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


@app.route('/add_message', methods=['POST'])
def add_message():
    if 'user_id' not in session:
        abort(401)  #권한 없는 요청
    if request.form['text']:
        g.db.execute('insert into message(author_id, text, pub_date) values(?, ?, ?)',
                     (session['user_id'], request.form['text'], int(time.time())))
        g.db.commit()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


# 이메일 주소를 해싱해서 아바타처럼 이미지를 보여주는 무료이미지 제공 서비스(gravatar) 사용
def gravatar_url(email, size=80):
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
           (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)

def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url


@app.route('/<username>/follow')
def follow_user(username):
    if not g.user:
        abort(401)  # 권한 없는 요청

    whom_id = get_user_id(username)

    if whom_id is None:
        abort(401)

    g.db.execute('insert into follower (who_id, whom_id) values(?, ?)',[session['user_id'], whom_id])
    g.db.commit()
    flash('You are now following "%s"' %username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/<username>/unfollow')
def unfollow_user(username):
    if not g.user:
        abort(401)

    whom_id = get_user_id(username)

    if whom_id is None:
        abort(401)

    g.db.execute('delete from follower where who_id=? and whom_id=?',[session['user_id'], whom_id])
    g.db.commit()
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/public')
def public_timeline():
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, USER
        where message.author_id = user_id
        order by message.pub_date desc limit ?''', [PER_PAGE]))


@app.route('/')
def timeline():
    if not g.user:
        return redirect(url_for('public_timeline'))

    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, USER
        where message.author_id = user.user_id and (
          user.user_id = ? OR
          user.user_id in (select whom_id from follower where who_id = ?)
          )
          order by message.pub_date desc limit ?''', [session['user_id'], session['user_id'], PER_PAGE]))


@app.route('/<username>')
def user_timeline(username):
    profile_user = query_db('select * from user where username=?',[username], one=True)
    if profile_user is None:
        abort(404)
    followed = False
    if g.user:
        followed = query_db('select 1 from follower where follower.who_id = ? and follower.whom_id = ?',
                            [session['user_id'], profile_user['user_id']], one=True) is not None

    return render_template('timeline.html', messages = query_db('''
        select message.*, user.* from message, user
        where user.user_id = message.author_id and user.user_id = ?
        order by message.pub_date desc limit ?''', [profile_user['user_id'], PER_PAGE]),
                           followed=followed, profile_user=profile_user)


if __name__ == '__main__':
    init_db()
    app.run()