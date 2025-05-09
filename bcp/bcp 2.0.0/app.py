from flask import Flask, request, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum
import enum
import xml.etree.ElementTree as ET

app = Flask(__name__)
# Using SQLite: the database file (app.db) will be created alongside this script
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Default admin credentials (override via env in production)
DEFAULT_ADMIN_EMAIL = 'admin@example.com'
DEFAULT_ADMIN_NAME = 'Administrator'
DEFAULT_ADMIN_PASSWORD = 'adminpass'

db = SQLAlchemy(app)

class UserRole(enum.Enum):
    USER = 'user'
    ADMIN = 'admin'
    RECRUITER = 'recruiter'

class UserStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    status = db.Column(SAEnum(UserStatus), default=UserStatus.PENDING, nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

# Helper for XML
def create_xml_response(root_tag, data_dict, status=200):
    root = ET.Element(root_tag)
    for key, val in data_dict.items():
        child = ET.SubElement(root, key)
        child.text = str(val)
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str, status)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Register a new user (role=USER, status=PENDING)
@app.route('/users', methods=['POST'])
def add_user():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    if not email or not name or not password:
        abort(400)
    if User.query.filter_by(email=email).first():
        return create_xml_response('error', {'message': 'Email already registered'}, 409)
    user = User(email=email, name=name, password=password)
    db.session.add(user)
    db.session.commit()
    return create_xml_response('user', {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role.value,
        'status': user.status.value
    }, 201)

# Admin: list users (optionally filter by status)
@app.route('/users', methods=['GET'])
def list_users():
    admin_email = request.args.get('admin_email')
    status_filter = request.args.get('status')
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    query = User.query
    if status_filter:
        try:
            s = UserStatus(status_filter)
            query = query.filter_by(status=s)
        except ValueError:
            abort(400)
    users = query.all()
    root = ET.Element('users')
    for u in users:
        e = ET.SubElement(root, 'user')
        ET.SubElement(e, 'id').text = str(u.id)
        ET.SubElement(e, 'email').text = u.email
        ET.SubElement(e, 'name').text = u.name
        ET.SubElement(e, 'role').text = u.role.value
        ET.SubElement(e, 'status').text = u.status.value
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Edit own profile (change name)
@app.route('/users/<int:user_id>', methods=['PUT'])
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
    new_name = request.form.get('name')
    if not new_name:
        abort(400)
    user.name = new_name
    db.session.commit()
    return create_xml_response('user', {'id': user.id, 'name': user.name})

# Admin: approve user
@app.route('/users/<int:user_id>/approve', methods=['PUT'])
def approve_user(user_id):
    admin_email = request.form.get('admin_email')
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    user = User.query.get_or_404(user_id)
    user.status = UserStatus.APPROVED
    db.session.commit()
    return create_xml_response('user', {'id': user.id, 'status': user.status.value})

# Admin: delete user
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    admin_email = request.form.get('admin_email')
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return create_xml_response('message', {'info': 'User deleted'})

# Admin: change role
@app.route('/users/<int:user_id>/role', methods=['PUT'])
def change_role(user_id):
    admin_email = request.form.get('admin_email')
    new_role = request.form.get('role')
    admin = User.query.filter_by(email=admin_email).first()
    if not admin or admin.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    user = User.query.get_or_404(user_id)
    try:
        user.role = UserRole(new_role)
    except ValueError:
        abort(400)
    db.session.commit()
    return create_xml_response('user', {'id': user.id, 'role': user.role.value})

# Recruiter: list all users
@app.route('/recruiter/users', methods=['GET'])
def recruiter_list_users():
    recruiter_email = request.args.get('recruiter_email')
    recruiter = User.query.filter_by(email=recruiter_email).first()
    if not recruiter or recruiter.role != UserRole.RECRUITER:
        return create_xml_response('error', {'message': 'Recruiter privileges required'}, 403)
    users = User.query.all()
    root = ET.Element('users')
    for u in users:
        e = ET.SubElement(root, 'user')
        ET.SubElement(e, 'id').text = str(u.id)
        ET.SubElement(e, 'email').text = u.email
        ET.SubElement(e, 'name').text = u.name
        ET.SubElement(e, 'role').text = u.role.value
        ET.SubElement(e, 'status').text = u.status.value
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Placeholder for job/application endpoints
@app.route('/jobs', methods=['GET'])
def list_jobs():
    pass

@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_job(job_id):
    pass

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed default admin if none exists
        if not User.query.filter_by(role=UserRole.ADMIN).first():
            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                name=DEFAULT_ADMIN_NAME,
                password=DEFAULT_ADMIN_PASSWORD,
                role=UserRole.ADMIN,
                status=UserStatus.APPROVED
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
