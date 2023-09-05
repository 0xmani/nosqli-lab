from flask_pymongo import PyMongo
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
import json
import jwt

app = Flask(__name__)

app.config['MONGO_URI'] = 'mongodb+srv://pogosat220:FnLFQQiFj32PtWwl@cluster0.a75lax3.mongodb.net/mydb?retryWrites=true&w=majority'
app.config['SECRET_KEY'] = 'secret'

jwt = JWTManager(app)
mongo = PyMongo(app)
users_collection = mongo.db.users 
books_collection = mongo.db.books 

# Routes

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', '')
    password = request.json.get('password', '')

    exist_user = users_collection.find_one({"username":username})

    if exist_user:
        return jsonify({"message": "User already exists"}), 400
    else:
        user = users_collection.insert_one({
            "username": username,
            "password": password,
            "created_at": datetime.utcnow()
        })
        
        return jsonify({"message": "User Created Successfully", "user": username}), 201


@app.route('/users', methods=['GET'])
@jwt_required()
def users():
    users = users_collection.find()

    user_data =[]

    for user in users:
        user_data.append({
            "Username": user['username'],
            "Created At": user['created_at']
            })
    return jsonify({
        "users": user_data
        }), 200

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', '')
    password = request.json.get('password', '')

    user = users_collection.find_one({"username":username, "password":password})

    if user:
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        access_token = create_access_token(identity=username)
        #token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'access_token': access_token, 'status':'success'}), 200

    return jsonify({'message': 'Invalid credentials', 'status': 'failed'}), 401

@app.route('/protected', methods=['GET'])
def protected_route():
    token = request.headers.get('Authorization')
    if token:
        token = token.split()[1]  
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return jsonify({'message': f'Hello, {payload["username"]}! This is a protected route.'}), 200
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
    return jsonify({'message': 'Token missing'}), 401


@app.route('/addbook', methods=['POST'])
@jwt_required()
def addbook():
    bookName = request.json.get("name", "")
    bookDescription = request.json.get("description", "")
    bookAuthor = request.json.get("author", "")

    book_exists = books_collection.find_one({"name": bookName})

    if book_exists:
        return jsonify({
            "status": "failed",
            "message": "Book already added!"
            }), 400
    else:
        book = books_collection.insert_one({
            "name": bookName,
            "description": bookDescription,
            "author": bookAuthor,
            "created_at": datetime.utcnow()
        })
        return jsonify({"status":"success", "message":"Book added Successfully!"}), 201


@app.route('/getbooks', methods=['GET'])
@jwt_required()
def getbooks():
    current_user = get_jwt_identity()
    books = books_collection.find({"added_by": current_user})

    book_data =[]

    for book in books:
        book_data.append({
            "name": book['name'],
            "description": book['description'],
            "author": book['author'],
            "created At": book['created_at']
            })
    return jsonify({
        "books": book_data
        }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
