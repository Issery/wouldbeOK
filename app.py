# -*- coding:utf-8 -*-
from numpy.core import overrides
from models import User
import pymssql
import pyodbc
import engine_conf
from flask import Flask, render_template, flash, request,  redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import urllib
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,SelectField
from wtforms.validators import DataRequired
import pandas as pd
import config
from sqlalchemy import text
import os


import sys
import imp
imp.reload(sys)


app = Flask(__name__)


# 数据库配置: 数据库地址/关闭自动跟踪修改
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://lancer:Lrd19970323@test1-server.database.windows.net/test1database?driver=ODBC+Driver+17+for+SQL+Server&charset=utf8'
# app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'lancer'

#--------------------------

#-----------------
# 创建数据库对象
# db = SQLAlchemy(app,session_options=sessionmaker(autocommit=False,autoflush=False,bind=engine))
db = SQLAlchemy(app)
# engine = create_engine(config.DB_URI)
# db.session = scoped_session(sessionmaker(autocommit=False,
#                                          autoflush=False,
#                                          bind=engine))
print('----------------engine initialized..--------------------------------------------------')
print(os.getcwd())
df = pd.read_csv('./static/people.csv')

'''
1. 配置数据库
    a. 导入SQLAlchemy扩展
    b. 创建db对象, 并配置参数
    c. 终端创建数据库
2. 添加书和作者模型
    a. 模型继承db.Model
    b. __tablename__:表名
    c. db.Column:字段
    d. db.relationship: 关系引用
3. 添加数据
4. 使用模板显示数据库查询的数据
    a. 查询所有的作者信息, 让信息传递给模板
    b. 模板中按照格式, 依次for循环作者和书籍即可 (作者获取书籍, 用的是关系引用)
5. 使用WTF显示表单
    a. 自定义表单类
    b. 模板中显示
    c. secret_key / 编码 / csrf_token
6. 实现相关的增删逻辑
    a. 增加数据
    b. 删除书籍  url_for的使用 /  for else的使用 / redirect的使用
    c. 删除作者 
'''
# 定义书和作者模型
# 作者模型



class peopleForm(FlaskForm):
    Attribute = SelectField(label='Attribute',
                            validators=[DataRequired('please select an attribute')],
                            choices=['salary','grade'])
    cpr = SelectField(label='comparator',
                      validators=[DataRequired('please select an attribute')],
                       choices=['>','<'])

    attr_value = StringField(label='value',validators=[DataRequired('please enter a value')])

    submit = SubmitField('search')

class UpForm(FlaskForm):
    name = SelectField(label='Name',
                            validators=[DataRequired('please select an attribute')],
                            choices=df['Name'])
    attr = SelectField(label='Attribute',
                      validators=[DataRequired('please select an attribute')],
                       choices=df.columns)

    value = StringField(label='value',validators=[DataRequired('please enter a value')])

    submit = SubmitField('Update')


class User(db.Model):
    # 表名
    __tablename__ = 'users'

    # 字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    state = db.Column(db.String(32))
    salary = db.Column(db.String(32))
    grade = db.Column(db.String(32))
    room = db.Column(db.String(32))
    telnum = db.Column(db.String(32))
    picture = db.Column(db.String(32))
    keywords = db.Column(db.String(300))

    def save(self):
        db.session.add(self)
        db.session.commit()




@app.route('/search', methods=['post'])
def search():
    seach_form = peopleForm(request.form)
    form_dict = request.form.to_dict()
    attr = form_dict.get("Attribute")
    cpr = form_dict.get("cpr")
    value = form_dict.get("attr_value")
    query = str(attr)+str(cpr)+str(value)
    people = User.query.filter(text(query))

    return render_template('result.html', people=people,df=df)



@app.route('/delete_person/<person_id>')
def delete_person(person_id):
    # 1. 查询数据库, 是否有该ID的书, 如果有就删除, 没有提示错误
    person = User.query.get(person_id)

    # 2. 如果有就删除
    if person:
        try:
            db.session.delete(person)
            db.session.commit()
            flash('Delete success')

        except Exception as e:
            print(e)
            flash('Delete failed')
            db.session.rollback()

    # redirect: 重定向, 需要传入网络/路由地址
    # url_for('index'): 需要传入视图函数名, 返回改视图函数对应的路由地址
    return redirect(url_for('index'))

@app.route('/update',methods=['post'])
def update():
    # 1. 查询数据库, 是否有该ID的书, 如果有就删除, 没有提示错误
    from_dict = request.form.to_dict()
    name = from_dict.get("name")
    attr = from_dict.get("attr").lower()
    value = from_dict.get("value")

    # 3. 判断作者是否存在
    person = User.query.filter_by(name=name).first()
    print(type(person))
    print(person)
    if person:
        try:
            res = User.query.filter_by(name=name).update({attr:value})
            db.session.commit()
            flash('update success')

        except Exception as e:
            print(e)
            flash('update failed')
            db.session.rollback()

    # redirect: 重定向, 需要传入网络/路由地址
    # url_for('index'): 需要传入视图函数名, 返回改视图函数对应的路由地址
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    # 创建自定义的表单类
    # author_form = AuthorForm()

    '''
    验证逻辑:
    1. 调用WTF的函数实现验证
    2. 验证通过获取数据
    3. 判断作者是否存在
    4. 如果作者存在, 判断书籍是否存在, 没有重复书籍就添加数据, 如果重复就提示错误
    5. 如果作者不存在, 添加作者和书籍
    6. 验证不通过就提示错误
    '''
    # 查询所有的作者信息, 让信息传递给模板
    people = User.query.all()
    form = peopleForm()
    form2 = UpForm()
    print(form.data)
    return render_template('book.html', people=people,df=df,form=form,form2=form2)


if __name__ == '__main__':
    # 删除表
    db.drop_all()
    # 创建表
    db.create_all()
    people_list = []
    df.fillna(' ', inplace=True)
    for idx in range(len(df)):
        person_name = df.iloc[idx]['Name']
        person_state = df.iloc[idx]['State']
        person_salary = df.iloc[idx]['Salary']
        person_grade = df.iloc[idx]['Grade']
        person_room = df.iloc[idx]['Room']
        person_telnum = df.iloc[idx]['Telnum']
        person_picture = df.iloc[idx]['Picture']
        person_keywords = df.iloc[idx]['Keywords']
        person = User(name=person_name,salary=person_salary,state=person_state,
                        grade=person_grade,room=person_room,telnum=person_telnum,picture=person_picture,
                        keywords=person_keywords)
        people_list.append(person)
    db.session.add_all(people_list)
    db.session.commit()
    app.run(debug=True)