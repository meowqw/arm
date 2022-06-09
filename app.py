from flask import Flask, render_template, request, redirect, make_response, session, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user
# from UserLogin import UserLogin
import requests
import os
import json
import datetime

app = Flask(__name__)
# login_manager = LoginManager(app)


app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:2110@localhost:3306/base?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
app_root = os.path.dirname(os.path.abspath(__file__))

# DB Model ROOMS


class Rooms(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    stage = db.Column(db.Integer(), nullable=False)
    section = db.Column(db.Integer(), nullable=False)
    type = db.Column(db.String(400), nullable=False)
    price = db.Column(db.Float(), nullable=False)


class Documents(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date_s = db.Column(db.DateTime(), nullable=False)
    date_e = db.Column(db.DateTime(), nullable=False)
    employer = db.Column(db.String(400), nullable=False)


class Residents(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    fio = db.Column(db.String(400), nullable=False)
    passport = db.Column(db.String(400), nullable=False)
    pass_who = db.Column(db.String(400), nullable=False)
    pass_d = db.Column(db.String(400), nullable=False)
    address = db.Column(db.String(400), nullable=False)
    bd = db.Column(db.DateTime(), nullable=False)
    contract = db.Column(db.Integer(), db.ForeignKey("documents.id"))
    room = db.Column(db.Integer(), db.ForeignKey("rooms.id"))


@app.route('/')
def index():
    """Главная страница"""

    return render_template('index.html')


@app.route('/residents', methods=['POST', 'GET'])
def residents():
    """Страница проживающие"""

    residents = Residents.query.all()
    contractList = [i.id for i in Documents.query.all()]
    roomList = [i.id for i in Rooms.query.all()]

    if request.method == "POST":

        db.session.add(Residents(fio=request.form['fio'],
                                 bd=request.form['bd'],
                                 passport=request.form['passport'],
                                 pass_who=request.form['pass_who'],
                                 pass_d=request.form['pass_d'],
                                 address=request.form['address'],
                                 contract=request.form['contract'],
                                 room=request.form['room']
                                 ))

        db.session.commit()

        return redirect(url_for('residents'))

    return render_template('residents.html', residents=residents, contractList=contractList, roomList=roomList)


@app.route('/edit/residents', methods=['POST', 'GET'])
def edit_residents():
    """Запрос на обнровление данных"""

    if request.method == "POST":
        data = request.get_json()
        resident = [i for i in data['data'].split('<>') if len(i) != 0]
        res = Residents.query.filter_by(id=data['id']).first()
        res.fio = resident[0]
        res.passport = resident[1]
        res.address = resident[2]
        res.bd = resident[3]
        res.contract = resident[4]
        db.session.commit()

    return redirect(url_for('residents'))


@app.route('/edit/rooms', methods=['POST', 'GET'])
def edit_rooms():
    """Запрос на обнровление данных"""

    if request.method == "POST":
        data = request.get_json()
        rooms = [i for i in data['data'].split('<>') if len(i) != 0]
        room = Rooms.query.filter_by(id=data['id']).first()
        room.stage = rooms[0]
        room.section = rooms[1]
        room.id = rooms[2]
        room.type = rooms[3]
        room.price = rooms[4]
        db.session.commit()

    return redirect(url_for('rooms'))


@app.route('/rooms', methods=['POST', 'GET'])
def rooms():
    """Страница комнаты"""

    ROOMS = Rooms.query.all()
    rooms = []
    for room in ROOMS:
        rooms.append([room, '\n'.join(
            [i.fio for i in Residents.query.filter_by(room=room.id).all()])])

    if request.method == "POST":

        db.session.add(Rooms(id=request.form['number'],
                             section=request.form['section'],
                             stage=request.form['stage'],
                             type=request.form['type'],
                             price=request.form['price']))

        db.session.commit()

        return redirect(url_for('rooms'))

    return render_template('rooms.html', rooms=rooms)


@app.route('/documents', methods=['POST', 'GET'])
def documents():
    """Станица документы"""

    DOCS = Documents.query.all()
    if request.method == "POST":

        db.session.add(Documents(id=request.form['number'],
                                 date_s=request.form['date_s'],
                                 date_e=request.form['date_e'],
                                 employer=request.form['employer']))

        db.session.commit()

        return redirect(url_for('documents'))

    return render_template('documents.html', documents=DOCS)


@app.route('/del/residents/<string:id>')
def del_residents(id):
    """Удаление проживающих"""

    Residents.query.filter_by(id=id).delete()
    db.session.commit()

    return redirect(url_for('residents'))


@app.route('/search/res', methods=['POST', 'GET'])
def search_residents():
    """Посик проживающих"""

    residents = Residents.query.all()
    contractList = [i.id for i in Documents.query.all()]
    roomList = [i.id for i in Rooms.query.all()]

    res = []
    if request.method == "POST":
        text = request.form['text'].lower()
        for i in residents:
            if (text in str(i.fio).lower()) or (text in str(i.passport).lower()) \
                    or (text in str(i.address).lower()) \
                    or (text in str(i.bd).lower()) or (text in str(i.contract).lower()) or (text in str(i.room).lower()):
                res.append(i)

    return render_template('residents.html', residents=res, contractList=contractList, roomList=roomList)


@app.route('/search/doc', methods=['POST', 'GET'])
def search_documents():
    """Посик документов"""

    DOCS = []

    docs = Documents.query.all()
    if request.method == "POST":
        text = request.form['text'].lower()
        for i in docs:
            if (text in str(i.id).lower()) or (text in str(i.date_s).lower()) or \
                    (text in str(i.date_e).lower()) or (text in str(i.employer).lower()):
                DOCS.append(i)

    return render_template('documents.html', documents=DOCS)


@app.route('/search/room', methods=['POST', 'GET'])
def search_rooms():
    """Посик комнат"""
    rooms_ = []
    rooms = Rooms.query.all()

    res = []
    
    if request.method == "POST":
        text = request.form['text'].lower()
        for i in rooms:
            if (text in str(i.stage).lower()) or (text in str(i.section).lower()) or \
                (text in str(i.id).lower()) or (text in str(i.type).lower()) or \
                    (text in str(i.price).lower()):
                res.append(i)
    if len(res) != 0:
        for room in res:
            rooms_.append([room, '\n'.join(
                [i.fio for i in Residents.query.filter_by(room=room.id).all()])])



    return render_template('rooms.html', rooms=rooms_)


if __name__ == '__main__':
    db.create_all()
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, port=5005)
    # Session(app)
