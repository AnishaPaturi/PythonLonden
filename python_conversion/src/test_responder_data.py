from flask import Blueprint, jsonify
from login_backend_python.extensions import db
from sqlalchemy import text

test_bp = Blueprint('test', __name__)

@test_bp.route('/api/test/responderFileData', methods=['GET'])
def test_responder_file_data():
    sql = text("SELECT * FROM responder_file LIMIT 10")
    result = db.session.execute(sql)
    data = [dict(row) for row in result]
    return jsonify(data)
