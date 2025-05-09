from flask import Flask, request, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import enum
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UserStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    status = db.Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

# Helper to build XML responses
def create_xml_response(root_tag, data_dict, status=200):
    root = ET.Element(root_tag)
    for key, val in data_dict.items():
        child = ET.SubElement(root, key)
        child.text = str(val)
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str, status)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/users', methods=['POST'])
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    if User.query.filter_by(username=username).first():
        return create_xml_response('error', {'message': 'User exists'}, 409)
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return create_xml_response('user', {'id': user.id, 'username': user.username, 'status': user.status.value}, 201)

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return create_xml_response('message', {'info': 'User deleted'})

@app.route('/users/<int:user_id>/approve', methods=['PUT'])
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = UserStatus.APPROVED
    db.session.commit()
    return create_xml_response('user', {'id': user.id, 'status': user.status.value})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return create_xml_response('error', {'message': 'Invalid credentials'}, 401)
    if user.status != UserStatus.APPROVED:
        return create_xml_response('error', {'message': 'Pending approval'}, 403)
    return create_xml_response('message', {'info': 'Login successful'})

@app.route('/jobs', methods=['GET'])
def list_jobs():
    jobs = Job.query.all()
    root = ET.Element('jobs')
    for job in jobs:
        j = ET.SubElement(root, 'job')
        ET.SubElement(j, 'id').text = str(job.id)
        ET.SubElement(j, 'title').text = job.title
        ET.SubElement(j, 'company').text = job.company
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_job(job_id):
    user_id = request.form.get('user_id')
    if not user_id:
        abort(400)
    user = User.query.get_or_404(int(user_id))
    if user.status != UserStatus.APPROVED:
        return create_xml_response('error', {'message': 'User not approved'}, 403)
    job = Job.query.get_or_404(job_id)
    application = Application(user_id=user.id, job_id=job.id)
    db.session.add(application)
    db.session.commit()
    return create_xml_response('application', {'application_id': application.id, 'status': 'received'})

if __name__ == '__main__':
    # Ensure tables are created within app context
    with app.app_context():
        db.create_all()
        # Seed sample jobs if none exist
        if Job.query.count() == 0:
            db.session.add_all([
                Job(title='Software Engineer', company='Acme Corp'),
                Job(title='Data Analyst', company='Data Inc'),
            ])
            db.session.commit()
    app.run(debug=True)

