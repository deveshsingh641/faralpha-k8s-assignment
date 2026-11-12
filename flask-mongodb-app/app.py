import os
from datetime import datetime
from urllib.parse import quote_plus
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

app = Flask(__name__)

def create_mongo_client():
    username = os.environ.get("MONGO_USERNAME")
    password = os.environ.get("MONGO_PASSWORD")
    host = os.environ.get("MONGO_HOST", "mongodb-service")
    port = os.environ.get("MONGO_PORT", "27017")
    database = os.environ.get("MONGO_DB", "flask_db")
    auth_source = os.environ.get("MONGO_AUTH_SOURCE", "admin")

    if username and password:
        user_enc = quote_plus(username)
        pass_enc = quote_plus(password)
        uri = f"mongodb://{user_enc}:{pass_enc}@{host}:{port}/{database}?authSource={auth_source}"
    else:
        uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client, database

client, db_name = create_mongo_client()
db = client[db_name]
collection = db["data"]

@app.route('/')
def index():
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

@app.route('/health')
def health():
    try:
        client.admin.command('ping')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except ConnectionFailure as err:
        return jsonify({"status": "unhealthy", "error": str(err)}), 503

@app.route('/data', methods=['GET', 'POST'])
def handle_data():
    if request.method == 'POST':
        payload = request.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        try:
            collection.insert_one(payload)
            return jsonify({"status": "Data inserted"}), 201
        except PyMongoError as err:
            return jsonify({"error": "Failed to write data", "details": str(err)}), 500

    try:
        records = list(collection.find({}, {"_id": 0}))
        return jsonify(records), 200
    except PyMongoError as err:
        return jsonify({"error": "Failed to read data", "details": str(err)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
