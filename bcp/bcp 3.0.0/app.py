from flask import Flask, request, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum
import enum
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

DEFAULT_ADMIN_EMAIL = 'admin@example.com'
DEFAULT_ADMIN_NAME = 'Administrator'
DEFAULT_ADMIN_PASSWORD = 'adminpass'

# --- ENUMS ---

class UserRole(enum.Enum):
    USER = 'user'
    ADMIN = 'admin'
    RECRUITER = 'recruiter'

class UserStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'

# --- MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    role = db.Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    status = db.Column(SAEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Text)
    skills = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

# --- UTILITY ---

def create_xml_response(root_tag, data_dict, status=200):
    root = ET.Element(root_tag)
    for key, val in data_dict.items():
        child = ET.SubElement(root, key)
        child.text = str(val)
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str, status)
    response.headers['Content-Type'] = 'application/xml'
    return response

# --- ROUTES ---

@app.route('/users', methods=['GET'])
def list_users():
    admin_email = request.args.get('admin_email')
    status_filter = request.args.get('status')
    
    # Validate admin
    if not admin_email:
        return create_xml_response('error', {'message': 'admin_email parameter is required'}, 400)
    
    admin = User.query.filter_by(
        email=admin_email,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    ).first()
    
    if not admin:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    
    # Filter users by status if provided
    query = User.query
    if status_filter:
        try:
            status = UserStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            abort(400)
    
    # Build XML response
    users = query.all()
    root = ET.Element('users')
    for user in users:
        user_elem = ET.SubElement(root, 'user')
        ET.SubElement(user_elem, 'id').text = str(user.id)
        ET.SubElement(user_elem, 'email').text = user.email
        ET.SubElement(user_elem, 'first_name').text = user.first_name
        ET.SubElement(user_elem, 'last_name').text = user.last_name
        ET.SubElement(user_elem, 'date_of_birth').text = user.date_of_birth
        ET.SubElement(user_elem, 'address').text = user.address
        ET.SubElement(user_elem, 'role').text = user.role.value
        ET.SubElement(user_elem, 'status').text = user.status.value
        
        # Include profile information
        if user.profile:
            profile_elem = ET.SubElement(user_elem, 'profile')
            ET.SubElement(profile_elem, 'summary').text = user.profile.summary or ''
            ET.SubElement(profile_elem, 'skills').text = user.profile.skills or ''
            ET.SubElement(profile_elem, 'education').text = user.profile.education or ''
            ET.SubElement(profile_elem, 'experience').text = user.profile.experience or ''
    
    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/users', methods=['POST'])
def add_user():
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    date_of_birth = request.form.get('date_of_birth')
    address = request.form.get('address')

    if not all([email, password, first_name, last_name, date_of_birth, address]):
        abort(400)

    if User.query.filter_by(email=email).first():
        return create_xml_response('error', {'message': 'Email already registered'}, 409)

    user = User(email=email, password=password, first_name=first_name,
                last_name=last_name, date_of_birth=date_of_birth, address=address)
    db.session.add(user)
    db.session.commit()

    profile = Profile(user_id=user.id)
    db.session.add(profile)
    db.session.commit()

    return create_xml_response('user', {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_of_birth': user.date_of_birth,
        'address': user.address,
        'role': user.role.value,
        'status': user.status.value
    }, 201)

# Admin: approve user
@app.route('/users/<int:user_id>/approve', methods=['PUT'])
def approve_user(user_id):
    admin_email = request.form.get('admin_email')
    
    # Validate admin
    admin = User.query.filter_by(
        email=admin_email,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    ).first()
    
    if not admin:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)
    
    # Get and update user
    user = User.query.get_or_404(user_id)
    user.status = UserStatus.APPROVED
    db.session.commit()
    
    return create_xml_response('user', {
        'id': user.id,
        'status': user.status.value
    })
    
# Edit user
@app.route('/users/<int:user_id>', methods=['PUT'])
def edit_profile(user_id):
    # Authentication
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return create_xml_response('error', {'message': 'Email and password required'}, 401)
    
    current_user = User.query.filter_by(email=email).first()
    
    # Validate credentials
    if not current_user or current_user.password != password:
        return create_xml_response('error', {'message': 'Invalid credentials'}, 403)
    
    # Authorization check
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Unauthorized access'}, 403)

    # Get user and profile
    user = User.query.get_or_404(user_id)
    profile = user.profile or Profile(user_id=user.id)

    # Update user fields
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.date_of_birth = request.form.get('date_of_birth', user.date_of_birth)
    user.address = request.form.get('address', user.address)

    # Update profile fields
    profile.summary = request.form.get('summary', profile.summary)
    profile.skills = request.form.get('skills', profile.skills)
    profile.education = request.form.get('education', profile.education)
    profile.experience = request.form.get('experience', profile.experience)

    db.session.commit()

    return create_xml_response('user', {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_of_birth': user.date_of_birth,
        'address': user.address,
        'summary': profile.summary or '',
        'skills': profile.skills or '',
        'education': profile.education or '',
        'experience': profile.experience or ''
    })

#Get user info 

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Authentication
    email = request.args.get('email')
    password = request.args.get('password')
    
    if not email or not password:
        return create_xml_response('error', {'message': 'Email and password required'}, 401)
    
    current_user = User.query.filter_by(email=email).first()
    
    # Validate credentials
    if not current_user or current_user.password != password:
        return create_xml_response('error', {'message': 'Invalid credentials'}, 403)
    
    # Authorization check
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        return create_xml_response('error', {'message': 'Unauthorized access'}, 403)

    # Get user data
    user = User.query.get_or_404(user_id)
    profile = user.profile
    
    return create_xml_response('user', {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_of_birth': user.date_of_birth,
        'address': user.address,
        'role': user.role.value,
        'status': user.status.value,
        'summary': profile.summary if profile else '',
        'skills': profile.skills if profile else '',
        'education': profile.education if profile else '',
        'experience': profile.experience if profile else ''
    })

# ... (keep other existing routes the same) ...

# --- INIT ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role=UserRole.ADMIN).first():
            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                first_name=DEFAULT_ADMIN_NAME,
                last_name="",
                date_of_birth="1990-01-01",
                address="Admin Address",
                role=UserRole.ADMIN,
                status=UserStatus.APPROVED
            )
            db.session.add(admin)
            db.session.commit()
            db.session.add(Profile(user_id=admin.id))
            db.session.commit()
        if not Job.query.first():
            job1 = Job(title="Software Engineer", company="Tech Corp")
            job2 = Job(title="Data Analyst", company="Data Inc")
            db.session.add_all([job1, job2])
            db.session.commit()
    app.run(debug=True)
