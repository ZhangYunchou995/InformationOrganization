# coding=utf-8
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, session
import pymysql
import os
import pandas as pd
from random import randint

from werkzeug.utils import redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


def get_cursor():
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'passwd': '12345678',
        'database': 'test',
        'unix_socket': "/tmp/mysql.sock"
    }
    conn = pymysql.connect(**config)
    conn.autocommit(1)  # conn.autocommit(True)
    return conn.cursor()


@app.route('/')
def index():
    if session.get('name'):
        return redirect('/login')
    else:
        return redirect('/index')

@app.route('/index')
def index2():
    session['name'] = None
    return render_template("index.html")

@app.route('/orderby_<item>')
def orderby(item):
    cursor = get_cursor()  # 打开数据库
    cursor.execute(f"select * from list order by {item} asc")
    lists = cursor.fetchall()
    lists = [list(_) for _ in lists]
    for x in lists:
        cursor.execute(f"select * from grade where id = {x[0]}")
        gradeList = cursor.fetchall()
        x.append("")
        x.append(gradeList)
        scores = 0
        credit = 0
        for g in gradeList:
            scores += g[3] * (g[2] / 20)
            credit += g[3]
        if credit != 0:
            x.append(scores / credit)
    return render_template("manage.html",name=session['name'],lists=lists,type=0,rands=randint(0, 999))

@app.route('/show_dormitory')
def show_dormitory():
    cursor = get_cursor()  # 打开数据库
    cursor.execute(f"select * from list order by sex asc, college asc, home desc")
    lists = cursor.fetchall()
    lists = [list(_) for _ in lists]
    i = 0
    for x in lists:
        cursor.execute(f"select * from grade where id = {x[0]}")
        gradeList = cursor.fetchall()
        if x[6] == "男": 
            x.append(f"B{600 + i // 4}")
        else:
            x.append(f"A{600 + i // 4}")
        x.append(gradeList)
        scores = 0
        credit = 0
        for g in gradeList:
            scores += g[3] * (g[2] / 20)
            credit += g[3]
        if credit != 0:
            x.append(scores / credit)
        i += 1
    return render_template("manage.html",name=session['name'],lists=lists,type=1,rands=randint(0, 999))

@app.route('/login', methods=['post', 'get'])
def login():
    cursor = get_cursor()  # 打开数据库
    cursor.execute("select COUNT(id) from list group by sex")
    sex = cursor.fetchall()
    sex0 = sex[0][0]
    sex1 = sex[1][0]
    election_data = {'Male': sex1, 'Female': sex0}
    candidate = [key for key in election_data]
    votes = [value for value in election_data.values()]
    plt.figure(figsize=(10, 10), dpi=100)
    plt.pie(votes, labels=candidate, autopct="%1.2f%%", colors=['c', 'm'],
        textprops={'fontsize': 24}, labeldistance=1.05)
    plt.legend(fontsize=16)
    plt.title(f"Male: Female = {sex1/sex0:.2f}:1", fontsize=24)
    plt.savefig("static/data.png")
    plt.close('all')

    if session.get('name'):
        cursor.execute("select * from list")
        lists = cursor.fetchall()
        lists = [list(_) for _ in lists]
        for x in lists:
            cursor.execute(f"select * from grade where id = {x[0]}")
            gradeList = cursor.fetchall()
            x.append("")
            x.append(gradeList)
            scores = 0
            credit = 0
            for g in gradeList:
                scores += g[3] * (g[2] / 20)
                credit += g[3]
            if credit != 0:
                x.append(scores / credit)
        return render_template("manage.html",name=session['name'],lists=lists,type=0,rands=randint(0, 999))
    name = request.form.get("name")
    password = request.form.get("password")
    if not name:
        msg = "您还没有登录"
        return render_template("index.html", msg=msg)
    row = cursor.execute("select * from manage where name = %s", (name))  # 获取查询到的信息条数
    if row:
        cursor.execute("select password from manage where name = %s", (name))
        message = cursor.fetchone()
        if password == str(message[0]):
            session['name'] = name
            return redirect('/')
        else:
            msg = "密码错误！"
            return render_template("index.html", msg=msg)
    else:
        msg = "您不是管理员！"
        return render_template("index.html", msg=msg)

@app.route('/insert', methods=['post'])
def insert():
    name = request.form.get("name")
    age = request.form.get("age")
    home = request.form.get("home")
    identity = request.form.get("identity")
    college = request.form.get("college")
    sex = request.form.get("sex")

    value = (name, age, home, identity, college, sex)
    insert_sql = '''INSERT INTO list(name,age,home,identity,college, sex) values (%s,%s,%s,%s,%s,%s)'''
    cursor = get_cursor()  # 打开数据库
    cursor.execute(insert_sql, value)  # 执行sql语句
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    cursor = get_cursor()  # 打开数据库
    cursor.execute("delete from list where id = %s", (id))  # 删除某一行值
    return redirect('/')

@app.route('/update',methods=['post'])
def update():
    id = request.form.get("id")
    name = request.form.get("name")
    age = request.form.get("age")
    home = request.form.get("home")
    identity = request.form.get("identity")
    college = request.form.get("college")
    sex = request.form.get("sex")
    value = (name, age, home, identity, college, sex, id)
    cursor = get_cursor() # 打开数据库
    cursor.execute("update list set name = %s,age = %s,home =%s,identity = %s,college = %s,sex = %s  where id = %s", value)  # 删除某一行值
    return redirect('/')

@app.route('/uploadGrade', methods=['post'])
def uploadGrade():
    f = request.files['gradeCSV']
    f.save('grade_temp.csv')
    grades = pd.read_csv('grade_temp.csv')
    cursor = get_cursor()
    values = grades.values.tolist()
    # 根据columns个数
    s = ','.join(['%s' for _ in range(len(grades.columns))])
    cursor.executemany('INSERT INTO {} VALUES ({})'.format("grade",s), values)
    return redirect('/')

if __name__ == '__main__':
    app.run()
