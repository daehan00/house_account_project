from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os
from pytz import timezone
from datetime import datetime

# Load environment variables
load_dotenv()

username = os.getenv("DATABASE_USERNAME")
password = os.getenv("DATABASE_PASSWORD")
host = os.getenv("DATABASE_HOST")
database = os.getenv("DATABASE_NAME")

SUPERUSER_IDS = set(int(id.strip()) for id in os.getenv('SUPERUSER_IDS').split(','))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{host}/{database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # CSRF 보호를 위한 비밀 키

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
    semester = db.Column(db.Integer, nullable=False)
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
    
class UserPassword(db.Model):
    __tablename__ = 'ra_user_password'
    user_id = db.Column(db.BigInteger, db.ForeignKey('ra_list_table.user_id'), primary_key=True)
    hashed_password = db.Column(db.Text, nullable=True)  # Initially null, set later

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

@app.route('/api/login', methods=['POST'])
@swag_from('swagger/login.yml')
def login():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        if not user_id or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        login = UserPassword.query.filter_by(user_id=user_id).first()
        if not login:
            return jsonify({'message': 'User does not exist'}), 404
        
        if not login.check_password(password):
            return jsonify({'message': 'Invalid Login', 'exists': False}), 401
        
        user = RAList.query.filter_by(user_id=user_id).first()
        return jsonify({'message': 'User exists', 'exists': True, 'authority': user.authority, 'user_id':user_id, 'user_name':user.user_name, 'user_data': str(user.year)+'-'+str(user.semester)+'-'+user.house_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/password/set', methods=['POST'])
@swag_from('swagger/password_set.yml')
def set_password():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        password = data.get('password')
        if not (user_id and user_name and password) :
            return jsonify({'message': 'Missing required user information'}), 400

        user = RAList.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.user_name != user_name:
            return jsonify({'message': 'User information does not match'}), 400
        
        user_password = UserPassword.query.filter_by(user_id=user_id).first()

        user_password.set_password(password)
        db.session.add(user_password)
        db.session.commit()
        return jsonify({'message': 'Password set successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route('/api/ra_list', methods=['POST'])
@swag_from('swagger/post_ra_list.yml', methods=['POST'])
def create_ra():
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")
    try:
        if RAList.query.filter_by(user_id=data.get('user_id')).first():
            return jsonify({"error": "RA with the provided user ID already exists"}), 409

        new_ra = RAList(
            user_id=data['user_id'],
            user_name=data['user_name'],
            user_num=data['user_num'],
            division_num=data.get('division_num'),
            email_address=data['email_address'],
            year=data['year'],
            semester=data['semester'],
            house_name=data['house_name'],
            authority=data.get('authority', False)
        )

        new_user_password = UserPassword(
            user_id=data['user_id'],
            hashed_password=None
        )
        db.session.add(new_ra)
        db.session.add(new_user_password)
        db.session.commit()
        return jsonify(new_ra.to_dict()), 201
    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ra_list/get', methods=['GET'])
@swag_from('swagger/get_ra_list.yml', methods=['GET'])
def get_all_ra():
    try:
        ra_list = RAList.query.all()
        if not ra_list:
            return jsonify({'message': 'No RA found'}), 404
        return jsonify([ra.to_dict() for ra in ra_list]), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ra_list/search', methods=['GET'])
@swag_from('swagger/search_ra_list.yml', methods=['GET'])
def search_ra():
    try:
        house_name = request.args.get('house_name')
        year = request.args.get('year', type=int)
        semester = request.args.get('semester', type=int)

        if not (house_name and year and semester):
            return jsonify({'message': 'Missing required parameters'}), 400

        query = RAList.query.filter(
            RAList.house_name == house_name,
            RAList.year == year,
            RAList.semester == semester,
            RAList.user_id.notin_(SUPERUSER_IDS)  # 슈퍼유저 ID 제외
        ).order_by(
            RAList.division_num.asc().nullslast(),
            RAList.user_name.asc().nullslast()
        )
        ra_list = query.all()

        if not ra_list:
            return jsonify({'message': 'No RA matches the provided criteria'}), 404

        return jsonify([ra.to_dict() for ra in ra_list]), 200

    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ra_list/update/<int:user_id>', methods=['PUT'])
@swag_from('swagger/put_ra_list.yml', methods=['PUT'])
def update_ra(user_id):
    try:
        data = request.get_json()
        ra = RAList.query.get_or_404(user_id)
        ra.authority = data.get('authority', ra.authority)
        ra.user_name = data.get('user_name', ra.user_name)
        ra.user_num = data.get('user_num', ra.user_num)
        ra.division_num = data.get('division_num', ra.division_num)
        ra.email_address = data.get('email_address', ra.email_address)
        ra.year = data.get('year', ra.year)
        ra.semester = data.get('semester', ra.semester)
        ra.house_name = data.get('house_name', ra.house_name)
        db.session.commit()
        return jsonify(ra.to_dict()), 200
    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ra_list/delete/<int:user_id>', methods=['DELETE'])
@swag_from('swagger/delete_ra_list.yml', methods=['DELETE'])
def delete_ra(user_id):
    if user_id in SUPERUSER_IDS:
        return jsonify({'message': 'Cannot delete this account'}), 403
    try:
        ra = RAList.query.get_or_404(user_id)
        user_password = UserPassword.query.get_or_404(user_id)

        db.session.delete(ra)
        db.session.delete(user_password)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/ra_list/delete_all', methods=['DELETE'])
def delete_all_ra():
    try:
        db.session.query(UserPassword).filter(UserPassword.user_id.notin_(SUPERUSER_IDS)).delete(synchronize_session=False)
        db.session.query(RAList).filter(RAList.user_id.notin_(SUPERUSER_IDS)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'message': 'All data deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ra_list/get/<int:user_id>', methods=['GET'])
@swag_from('swagger/get_ra.yml', methods=['GET'])
def get_ra(user_id):
    ra = RAList.query.get_or_404(user_id)
    return jsonify(ra.to_dict()), 200

class Program(db.Model):
    __tablename__ = 'program_list_table'
    program_id = db.Column(db.Text, primary_key=True)
    program_name = db.Column(db.Text, nullable=False)
    house_name = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    register_check = db.Column(db.Boolean)
    year_semester_house = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "program_id": self.program_id,
            "program_name": self.program_name,
            "house_name": self.house_name,
            "year": self.year,
            "semester": self.semester,
            "register_check": self.register_check,
            "year_semester_house": self.year_semester_house
        }


@app.route('/api/program', methods=['POST'])
@swag_from('swagger/post_program.yml', methods=['POST'])
def create_program():
    try:
        data = request.get_json()
        if not data:
            abort(400, description="No data provided.")

        existing_program = Program.query.filter_by(program_id=data['program_id']).first()
        if existing_program:
            return jsonify({"error": "Program with the provided program ID already exists"}), 409

        new_program = Program(
            program_id=data['program_id'],
            program_name=data['program_name'],
            house_name=data['house_name'],
            year=data['year'],
            semester=data['semester'],
            register_check=data.get('register_check', True),
            year_semester_house=data['year_semester_house']
        )
        db.session.add(new_program)
        db.session.commit()
        return jsonify(new_program.to_dict()), 201
    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/program', methods=['DELETE'])
@swag_from('swagger/delete_program.yml', methods=['DELETE'])
def delete_program():
    try:
        year_semester_house = request.args.get('year_semester_house')
        result = Program.query.filter_by(year_semester_house=year_semester_house).delete()
        if result == 0:
            return jsonify({"message": "No programs found with the specified key"}), 404
        db.session.commit()
        return jsonify({"message": "Programs deleted"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/program', methods=['GET'])
@swag_from('swagger/get_program.yml', methods=['GET'])
def get_program():
    try:
        year_semester_house = request.args.get('year_semester_house')
        programs = Program.query.filter_by(year_semester_house=year_semester_house).all()
        if not programs:
            return jsonify({'message': 'No programs found'}), 404
        return jsonify([program.to_dict() for program in programs]), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


class ReceiptSubmission(db.Model):
    __tablename__ = 'receipt_submissions_table'
    id = db.Column(db.Text, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    time = db.Column(db.Text, nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=True), nullable=False)
    house_name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('ra_list_table.user_id'), nullable=False)
    program_id = db.Column(db.Text, db.ForeignKey('program_list_table.program_id'), nullable=False)
    category_id = db.Column(db.Text, nullable=False)
    head_count = db.Column(db.Integer, nullable=False)
    expenditure = db.Column(db.BigInteger, nullable=False)
    store_name = db.Column(db.Text, nullable=False)
    division_num = db.Column(db.Text)
    reason_store = db.Column(db.Text, nullable=False)
    isp_check = db.Column(db.Boolean, nullable=False)
    holiday_check = db.Column(db.Boolean, nullable=False)
    souvenir_record = db.Column(db.Boolean, nullable=False)
    division_program = db.Column(db.Boolean, nullable=False)
    purchase_reason = db.Column(db.Text, nullable=False)
    key_items_quantity = db.Column(db.Text, nullable=False)
    purchase_details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.now(timezone('Asia/Seoul')))
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.now(timezone('Asia/Seoul')), onupdate=datetime.now(timezone('Asia/Seoul')))
    warning_division = db.Column(db.Text)

    ra = relationship("RAList", backref="receipts")
    program = relationship("Program", backref="receipts")

    def to_dict(self):
        return {
            column.name: getattr(self, column.name).isoformat() if isinstance(getattr(self, column.name), datetime) else getattr(self, column.name)
            for column in self.__class__.__table__.columns
        }

@app.route('/api/receipts', methods=['POST'])
@swag_from('swagger/post_receipt.yml', methods=['POST'])
def create_receipt():
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")

    # Define the required fields for a ReceiptSubmission
    required_fields = ['id', 'year', 'month', 'day', 'time', 'date', 'house_name',
                       'user_id', 'program_id', 'category_id', 'head_count', 'expenditure',
                       'store_name', 'reason_store', 'isp_check', 'holiday_check',
                       'souvenir_record', 'division_program', 'purchase_reason',
                       'key_items_quantity', 'purchase_details']

    # Check if all required fields are present in the incoming data
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': 'Missing required data fields', 'missing_fields': missing_fields}), 400

    try:
        receipt = ReceiptSubmission(**data)
        db.session.add(receipt)
        db.session.commit()
        return jsonify(receipt.to_dict()), 201
    except IntegrityError as e:
        db.session.rollback()
        # Check if the error is caused by a duplicate key violation
        if 'duplicate key value' in str(e.orig):
            return jsonify({'error': 'ID already exists, duplicate entry'}), 400
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/receipts/house/<house_name>', methods=['GET'])
@swag_from('swagger/get_receipts_by_house.yml')
def get_receipts_by_house(house_name):
    try:
        receipts = db.session.query(ReceiptSubmission).join(RAList).join(Program).filter(
            ReceiptSubmission.house_name == house_name
        ).all()
        if not receipts:
            abort(404, description=f"No receipts found for house name {house_name}")

        results = []
        for receipt in receipts:
            receipt_dict = receipt.to_dict()
            receipt_dict['user_name'] = receipt.ra.user_name
            receipt_dict['program_name'] = receipt.program.program_name
            results.append(receipt_dict)

        return jsonify(results), 200
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/receipts/house/<house_name>/year/<int:year>/month/<int:month>', methods=['GET'])
@swag_from('swagger/get_receipts_house_year_month.yml')
def get_receipts_by_house_year_month(house_name, year, month):
    try:
        receipts = db.session.query(ReceiptSubmission).join(RAList).join(Program).filter(
            ReceiptSubmission.house_name == house_name,
            ReceiptSubmission.year == year,
            ReceiptSubmission.month == month
        ).all()
        if not receipts:
            abort(404, description=f"No receipts found for house name {house_name} in {year}-{month}")

        results = []
        for receipt in receipts:
            receipt_dict = receipt.to_dict()
            receipt_dict['user_name'] = receipt.ra.user_name
            receipt_dict['program_name'] = receipt.program.program_name
            results.append(receipt_dict)

        return jsonify(results), 200
    except Exception as e:
        abort(500, description=str(e))


@app.route('/api/receipts/user/<int:user_id>', methods=['GET'])
@swag_from('swagger/get_receipts_by_user.yml')
def get_receipts_by_user(user_id):
    try:
        receipts = db.session.query(ReceiptSubmission).join(RAList).join(Program).filter(
            ReceiptSubmission.user_id == user_id
        ).all()
        if not receipts:
            abort(404, description=f"No receipts found for user ID {user_id}")

        results = []
        for receipt in receipts:
            receipt_dict = receipt.to_dict()
            receipt_dict['user_name'] = receipt.ra.user_name
            receipt_dict['program_name'] = receipt.program.program_name
            results.append(receipt_dict)

        return jsonify(results), 200
    except Exception as e:
        abort(500, description=str(e))

@app.route('/api/receipts/<receipt_id>', methods=['DELETE'])
@swag_from('swagger/delete_receipt.yml')
def delete_receipt(receipt_id):
    try:
        receipt = ReceiptSubmission.query.get(receipt_id)
        if not receipt:
            abort(404, description=f"Receipt with ID {receipt_id} not found")
        db.session.delete(receipt)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))



class CardReservation(db.Model):
    __tablename__ = 'card_reservations_table'

    id = db.Column(db.Integer, primary_key=True)
    house_name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Text, nullable=False)
    start_datetime = db.Column(db.TIMESTAMP, nullable=False)
    end_datetime = db.Column(db.TIMESTAMP, nullable=False)
    isp_card = db.Column(db.Boolean, nullable=False)
    program_id = db.Column(db.Text, nullable=False)
    weekend_night_usage = db.Column(db.Boolean, nullable=True)
    purpose = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.now(timezone('Asia/Seoul')))
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=datetime.now(timezone('Asia/Seoul')),
                           onupdate=datetime.now(timezone('Asia/Seoul')))

    def to_dict(self):
        return {
            "id": self.id,
            "house_name": self.house_name,
            "user_id": self.user_id,
            "start_datetime": self.start_datetime.isoformat(),
            "end_datetime": self.end_datetime.isoformat(),
            "isp_card": self.isp_card,
            "weekend_night_usage": self.weekend_night_usage,
            "program_id": self.program_id,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@app.route('/api/calendar/create', methods=['POST'])
@swag_from('swagger/calendar_create.yml')
def create_reservation():
    data = request.json
    try:
        new_reservation = CardReservation(
            house_name=data['house_name'],
            user_id=data['user_id'],
            start_datetime=data['start_datetime'],
            end_datetime=data['end_datetime'],
            isp_card=data['isp_card'],
            weekend_night_usage=data.get('weekend_night_usage'),
            program_id=data['program_id'],
            purpose=data.get('purpose')
        )
        db.session.add(new_reservation)
        db.session.commit()
        return jsonify(new_reservation.id), 201
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))

@app.route('/api/calendar/update/<int:id>', methods=['PUT'])
@swag_from('swagger/calendar_update.yml')
def update_reservation(id):
    reservation = CardReservation.query.get(id)
    if not reservation:
        abort(404, description="Reservation not found")

    data = request.json
    try:
        reservation.house_name = data.get('house_name', reservation.house_name)
        reservation.user_id = data.get('user_id', reservation.user_id)
        reservation.start_datetime = data.get('start_datetime', reservation.start_datetime)
        reservation.end_datetime = data.get('end_datetime', reservation.end_datetime)
        reservation.isp_card = data.get('isp_card', reservation.isp_card)
        reservation.weekend_night_usage = data.get('weekend_night_usage', reservation.weekend_night_usage)
        reservation.program_id = data.get('program_id', reservation.program_id)
        reservation.purpose = data.get('purpose', reservation.purpose)

        db.session.commit()
        return jsonify({"message": "Reservation updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))

@app.route('/api/calendar/all', methods=['GET'])
@swag_from('swagger/calendar_get_all.yml')
def get_reservations():
    try:
        reservations = CardReservation.query.all()
        return jsonify([reservation.to_dict() for reservation in reservations]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/house/<house_name>', methods=['GET'])
@swag_from('swagger/calendar_get_by_house.yml')
def get_reservations_by_house(house_name):
    try:
        reservations = CardReservation.query.filter_by(house_name=house_name).all()
        if reservations:
            return jsonify([reservation.to_dict() for reservation in reservations]), 200
        else:
            return jsonify({"message": "No reservations found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/delete/<int:id>', methods=['DELETE'])
@swag_from('swagger/calendar_delete.yml')
def delete_reservation(id):
    reservation = CardReservation.query.get(id)
    if not reservation:
        return jsonify({"message": "Reservation not found"}), 404

    try:
        db.session.delete(reservation)
        db.session.commit()
        return jsonify({"message": "Reservation deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendar/verify/<int:event_id>', methods=['GET'])
@swag_from('swagger/calendar_verify.yml')
def verify_reservation_submitter(event_id):
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    reservation = CardReservation.query.get(event_id)
    if not reservation:
        return jsonify({"message": "Reservation not found"}), 404

    if reservation.user_id == user_id:
        return jsonify({"message": "Valid submitter"}), 200
    else:
        return jsonify({"message": "Unauthorized"}), 403


class ReportDetail(db.Model):
    __tablename__ = 'report_details'
    id = db.Column(db.Integer, primary_key=True)
    year_semester_house = db.Column(db.Text, nullable=False)
    week = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.BigInteger, nullable=False)
    category_contents = db.Column(db.JSON, nullable=False)
    common = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'year_semester_house': self.year_semester_house,
            'week': self.week,
            'user_id': self.user_id,
            'category_contents': self.category_contents,
            'common': self.common
        }


@app.route('/api/report_details', methods=['POST'])
@swag_from('swagger/post_report_details.yml')
def create_report_detail():
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")

    try:
        # 중복 확인을 위한 쿼리
        existing_report_detail = ReportDetail.query.filter_by(
            year_semester_house=data['year_semester_house'],
            week=data['week'],
            user_id=data['user_id']
        ).first()

        # 중복된 데이터가 있는 경우 에러 반환
        if existing_report_detail:
            return jsonify({"error": "Already submitted."}), 400

        # 새로운 ReportDetail 객체 생성 및 데이터베이스에 추가
        new_report_detail = ReportDetail(
            year_semester_house=data['year_semester_house'],
            week=data['week'],
            user_id=data['user_id'],
            category_contents=data['category_contents'],
            common=data['common']
        )
        db.session.add(new_report_detail)
        db.session.commit()
        return jsonify(new_report_detail.to_dict()), 201

    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/report_details/week', methods=['GET'])
@swag_from('swagger/get_report_details_week.yml')
def get_reports_by_week():
    year_semester_house = request.args.get('year_semester_house')
    week = request.args.get('week')
    if not year_semester_house or not week:
        abort(400, description="Missing required parameters: year_semester_house and week.")

    reports = ReportDetail.query.filter_by(year_semester_house=year_semester_house, week=week).all()
    if reports:
        return jsonify([report.to_dict() for report in reports]), 200
    else:
        return jsonify({'message': 'No reports found'}), 404

@app.route('/api/report_details/user', methods=['GET'])
@swag_from('swagger/get_report_details_user.yml')
def get_reports_by_user():
    year_semester_house = request.args.get('year_semester_house')
    user_id = request.args.get('user_id', type=int)
    if not year_semester_house or not user_id:
        abort(400, description="Missing required parameters: year_semester_house and user_id.")

    reports = ReportDetail.query.filter_by(year_semester_house=year_semester_house, user_id=user_id).all()
    if reports:
        return jsonify([report.to_dict() for report in reports]), 200
    else:
        return jsonify({'message': 'No reports found'}), 404

@app.route('/api/report_details/<int:id>', methods=['PUT'])
@swag_from('swagger/put_report_details.yml')
def update_report_detail(id):
    data = request.get_json()
    report = ReportDetail.query.get(id)
    if not report:
        return jsonify({'message': 'Report not found'}), 404

    try:
        # category_contents 필드만 업데이트
        if 'category_contents' in data:
            report.category_contents = data['category_contents']
        else:
            return jsonify({"error": "Missing data: category_contents required"}), 400

        db.session.commit()
        return jsonify(report.to_dict()), 200
    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Missing data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/report_details/<int:id>', methods=['DELETE'])
@swag_from('swagger/delete_report_details.yml')
def delete_report_detail(id):
    report = ReportDetail.query.get(id)
    if not report:
        return jsonify({'message': 'Report not found'}), 404

    try:
        db.session.delete(report)
        db.session.commit()
        return '', 204  # HTTP 204 No Content: 응답에 본문 데이터가 없을 때 사용
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
