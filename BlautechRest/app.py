import firebase_admin
import pymongo
import pyrebase
from flask_pymongo import PyMongo
from firebase_admin import credentials, auth, firestore
import json
from pymongo import MongoClient
from flask import Flask, request
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
cliente = MongoClient('mongodb+srv://emily:Mily9812$@cluster0.skqxh.mongodb.net/BLAUTECH')
cursor = cliente['BLAUTECH']
mongoDb = cursor['USERS']

cred = credentials.Certificate('firebaseAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('authConfig.json')))
db = firestore.client()



def check_token(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not request.headers.get('authorization'):
            return {'message': 'No token provided'}, 400
        try:
            user = auth.verify_id_token(request.headers['authorization'])
            request.user = user
        except:
            return {'message': 'Invalid token provided.'}, 400
        return f(*args, **kwargs)

    return wrap


@app.route('/blautechApi/getUserInfo',methods=['POST'])
@check_token
def userInfor():
    email = request.form.get('email')
    user = auth.get_user_by_email(email)
    return {'nombre:': user.display_name, 'uid': user.uid, 'email': user.email}, 200


@app.route('/blautechApi/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    display_name = request.form.get('name')

    if email is None or password is None:
        return {'message': 'Error missing email or password'}, 400

    try:

        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            disabled=False
        )
        doc_ref = db.collection(u'users').document(user.uid)
        doc_ref.set({
            u'nombre': user.display_name,
            u'email': user.email,
            u'disabled': False
        })
        response = mongoDb.insert_one({
            u'_id': user.uid,
            u'nombre': user.display_name,
            u'email': user.email,
            u'disabled': False})
        print(response.inserted_id)

        return {'message': f'Successfully created user {user.uid}'}, 200
    except:
        return {'message': 'Error creating user'}, 400


@app.route('/blautechApi/updateUser',methods=['PUT'])
@check_token
def updateUser():
    uid = request.form.get('uid')
    email = request.form.get('email')
    password = request.form.get('password')
    display_name = request.form.get('name')
    disabledStr = request.form.get('disabled')

    if email is None or password is None:
        return {'message': 'Error missing email or password'}, 400

    try:
        disabled = False
        if (disabledStr == 'False'):
            disabled = False
        else:
            disabled = True
        print(uid)
        user = auth.update_user(
                                uid,
                                email=email,
                                password=password,
                                display_name=display_name,
                                disabled=disabled)

        doc_ref = db.collection(u'users').document(uid)
        doc_ref.update({
            u'nombre': display_name,
            u'email': email,
            u'disabled': disabled
        })

        mongoDb.update_one(
            {u'_id': uid},
            {
                '$set': {
                    u'_id': uid,
                    u'nombre': display_name,
                    u'email': email,
                    u'disabled': disabled
                }
            })

        return {'message': f' Actualizando satisfactorio de usuario {user.uid}'}, 200
    except:
        return {'message': 'Error actualizando  usuario '}, 400


@app.route('/blautechApi/deleteUser',methods=['POST'])
@check_token
def deleteUser():
    uid = request.form.get('uid')
    try:
        print(uid);
        auth.delete_user(uid)
        db.collection(u'users').document(uid).delete()
        mongoDb.delete_one({u'_id': uid})

        return {'message': f'Borrado correcto de usuario'}, 200
    except:
        return {'message': 'Error en borrado de usuario'}, 400

@app.route('/blautechApi/listUsers',methods=['GET'])
@check_token
def listUsers():
    try:
        users = []
        for user in auth.list_users().iterate_all():
            users.append({'uid': user.uid, 'email': user.email, 'nombre': user.display_name, 'disabled': user.disabled})

        return {'users': users}, 200
    except:
        return {'message': 'Error al obtener lista de usuarios'}, 400


@app.route('/blautechApi/token',methods=['POST'])
def token():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return {'token': jwt}, 200
    except:
        return {'message': 'Error en el logeo'}, 400


if __name__ == '__main__':
    app.run(debug=True)
