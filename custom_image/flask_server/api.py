from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

username = os.getenv("DATABASE_USERNAME")
password = os.getenv("DATABASE_PASSWORD")
host = os.getenv("DATABASE_HOST")
database = os.getenv("DATABASE_NAME")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{host}/{database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
swagger = Swagger(app, template_file='swagger/swagger.yml')

class RAList(db.Model):
    __tablename__ = 'ra_list_table'
    user_id = db.Column(db.BigInteger, primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    user_num = db.Column(db.Text, nullable=False)
    division_num = db.Column(db.Integer)
    email_address = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Boolean, nullable=False)
    house_name = db.Column(db.Text, nullable=False)
    authority = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_num': self.user_num,
            'division_num': self.division_num,
            'email_address': self.email_address,
            'year': self.year,
            'semester': self.semester,
            'house_name': self.house_name,  # 새로운 필드 포함
            'authority': self.authority
        }

@app.route('/api/ra_list', methods=['POST'])
@swag_from('swagger/post_ra_list.yml', methods=['POST'])
def create_ra():
    data = request.get_json()
    new_ra = RAList(
        user_id=data['user_id'],
        user_name=data['user_name'],
        user_num=data['user_num'],
        division_num=data.get('division_num'),
        email_address=data['email_address'],
        year=data['year'],
        semester=data['semester'],
        house_name=data['house_name'],
        authority=data['authority']
    )
    db.session.add(new_ra)
    db.session.commit()
    return jsonify(new_ra.to_dict()), 201

@app.route('/api/ra_list', methods=['GET'])
@swag_from('swagger/get_ra_list.yml', methods=['GET'])
def get_all_ra():
    ra_list = RAList.query.all()
    return jsonify([ra.to_dict() for ra in ra_list]), 200

@app.route('/api/check_user/<int:user_id>', methods=['GET'])
@swag_from('swagger/check_user.yml')
def check_user(user_id):
    user = RAList.query.get(user_id)
    if user:
        return jsonify({'message': 'User exists', 'exists': True}), 200
    else:
        return jsonify({'message': 'User does not exist', 'exists': False}), 404

@app.route('/api/ra_list/<int:user_id>', methods=['PUT'])
@swag_from('swagger/put_ra_list.yml', methods=['PUT'])
def update_ra(user_id):
    data = request.get_json()
    ra = RAList.query.get_or_404(user_id)
    ra.user_name = data.get('user_name', ra.user_name)
    ra.user_num = data.get('user_num', ra.user_num)
    ra.division_num = data.get('division_num', ra.division_num)
    ra.email_address = data.get('email_address', ra.email_address)
    ra.year = data.get('year', ra.year)
    ra.semester = data.get('semester', ra.semester)
    ra.house_name = data.get('house_name', ra.house_name)  # 새로운 필드 포함
    db.session.commit()
    return jsonify(ra.to_dict()), 200

@app.route('/api/ra_list/<int:user_id>', methods=['DELETE'])
@swag_from('swagger/delete_ra_list.yml', methods=['DELETE'])
def delete_ra(user_id):
    ra = RAList.query.get_or_404(user_id)
    db.session.delete(ra)
    db.session.commit()
    return '', 204

@app.route('/api/ra_list/<int:user_id>', methods=['GET'])
@swag_from('swagger/get_ra.yml', methods=['GET'])
def get_ra(user_id):
    ra = RAList.query.get_or_404(user_id)
    return jsonify(ra.to_dict()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
