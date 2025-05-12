from flask import Flask, request, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SAEnum
import enum
import xml.etree.ElementTree as ET
from email_validator import validate_email, EmailNotValidError

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
    
class JobStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'

class ApplicationStatus(enum.Enum):
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
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False)
    posting_date = db.Column(db.String(10), nullable=False)
    status = db.Column(SAEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
     
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False)

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

from email_validator import validate_email, EmailNotValidError

@app.route('/users', methods=['POST'])
def add_user():
    # Get form data
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    date_of_birth = request.form.get('date_of_birth')
    address = request.form.get('address')

    # Validate required fields
    if not all([email, password, first_name, last_name, date_of_birth, address]):
        return create_xml_response('error', {'message': 'All fields are required'}, 400)

    # Validate and normalize email
    try:
        valid = validate_email(email)
        email = valid.email  # Normalized form
    except EmailNotValidError as e:
        return create_xml_response('error', {'message': str(e)}, 400)

    # Check for existing user
    if User.query.filter_by(email=email).first():
        return create_xml_response('error', {'message': 'Email already registered'}, 409)

    # Create new user with normalized email
    user = User(
        email=email,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        date_of_birth=date_of_birth.strip(),
        address=address.strip()
    )
    
    db.session.add(user)
    db.session.commit()

    # Create empty profile
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
    
# Admin: delete user
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Admin validation
    admin_email = request.form.get('admin_email')
    
    admin = User.query.filter_by(
        email=admin_email,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    ).first()
    
    if not admin:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)

    # Get and delete user
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return create_xml_response('message', {
        'info': f'User {user_id} deleted successfully'
    })
    
    # Recruiter: Create Job
@app.route('/jobs', methods=['POST'])
def create_job():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Authentication
    recruiter = User.query.filter_by(
        email=email,
        password=password,
        role=UserRole.RECRUITER,
        status=UserStatus.APPROVED
    ).first()
    
    if not recruiter:
        return create_xml_response('error', {'message': 'Invalid recruiter credentials'}, 403)

    title = request.form.get('title')
    company = request.form.get('company')
    description = request.form.get('description')
    required_skills = request.form.get('required_skills')
    posting_date = request.form.get('posting_date')

    if not all([title, company, description, required_skills, posting_date]):
        abort(400)

    job = Job(
        title=title,
        company=company,
        description=description,
        required_skills=required_skills,
        posting_date=posting_date,
        recruiter_id=recruiter.id
    )
    db.session.add(job)
    db.session.commit()

    return create_xml_response('job', {
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'status': job.status.value
    }, 201)

# Admin: Approve Job
@app.route('/jobs/<int:job_id>/approve', methods=['PUT'])
def approve_job(job_id):
    admin_email = request.form.get('admin_email')
    
    admin = User.query.filter_by(
        email=admin_email,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    ).first()
    
    if not admin:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)

    job = Job.query.get_or_404(job_id)
    job.status = JobStatus.APPROVED
    db.session.commit()
    
    return create_xml_response('job', {
        'id': job.id,
        'status': job.status.value
    })

# Recruiter: Manage Jobs
@app.route('/jobs/<int:job_id>', methods=['PUT', 'DELETE'])
def manage_job(job_id):
    email = request.form.get('email')
    password = request.form.get('password')
    
    recruiter = User.query.filter_by(
        email=email,
        password=password,
        role=UserRole.RECRUITER,
        status=UserStatus.APPROVED
    ).first()
    
    if not recruiter:
        return create_xml_response('error', {'message': 'Invalid recruiter credentials'}, 403)

    job = Job.query.filter_by(id=job_id, recruiter_id=recruiter.id).first()
    if not job:
        abort(404)

    if request.method == 'PUT':
        job.title = request.form.get('title', job.title)
        job.company = request.form.get('company', job.company)
        job.description = request.form.get('description', job.description)
        job.required_skills = request.form.get('required_skills', job.required_skills)
        job.posting_date = request.form.get('posting_date', job.posting_date)
        db.session.commit()
        return create_xml_response('job', {
            'id': job.id,
            'title': job.title,
            'status': job.status.value
        })

    elif request.method == 'DELETE':
        db.session.delete(job)
        db.session.commit()
        return create_xml_response('message', {'info': f'Job {job_id} deleted'})

# User: Apply for Job
@app.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_job(job_id):
    transfer_encoding = request.headers.get('Transfer-Encoding', '')
    if 'chunked' in transfer_encoding.lower():
        return create_xml_response('error', {'message': 'unknown error occurred'}, 400)

    # Existing code below
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(
        email=email,
        password=password,
        status=UserStatus.APPROVED
    ).first()
    
    if not user:
        return create_xml_response('error', {'message': 'Invalid user credentials'}, 403)

    job = Job.query.filter_by(id=job_id, status=JobStatus.APPROVED).first()
    if not job:
        return create_xml_response('error', {'message': 'Job not available'}, 404)

    existing_application = Application.query.filter_by(
        user_id=user.id,
        job_id=job_id
    ).first()
    
    if existing_application:
        return create_xml_response('error', {'message': 'Already applied'}, 409)

    application = Application(user_id=user.id, job_id=job_id)
    db.session.add(application)
    db.session.commit()

    return create_xml_response('application', {
        'id': application.id,
        'job_id': job_id,
        'status': application.status.value
    }, 201)

# Recruiter: View Applications
@app.route('/jobs/<int:job_id>/applications', methods=['GET'])
def view_applications(job_id):
    transfer_encoding = request.headers.get('Transfer-Encoding', '')
    if 'chunked' in transfer_encoding.lower():
        return create_xml_response('error', {'message': 'unknown error occurred'}, 400)
    email = request.args.get('email')
    password = request.args.get('password')
    
    recruiter = User.query.filter_by(
        email=email,
        password=password,
        role=UserRole.RECRUITER,
        status=UserStatus.APPROVED
    ).first()
    
    if not recruiter:
        return create_xml_response('error', {'message': 'Invalid recruiter credentials'}, 403)

    job = Job.query.filter_by(id=job_id, recruiter_id=recruiter.id).first()
    if not job:
        abort(404)

    applications = Application.query.filter_by(job_id=job_id).all()
    
    root = ET.Element('applications')
    for app in applications:
        app_elem = ET.SubElement(root, 'application')
        ET.SubElement(app_elem, 'id').text = str(app.id)
        ET.SubElement(app_elem, 'user_id').text = str(app.user_id)
        ET.SubElement(app_elem, 'status').text = app.status.value
        
        user = User.query.get(app.user_id)
        if user and user.profile:
            ET.SubElement(app_elem, 'summary').text = user.profile.summary or ''
            ET.SubElement(app_elem, 'skills').text = user.profile.skills or ''

    xml_str = ET.tostring(root)
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

# User: View Applications
@app.route('/applications', methods=['GET'])
def user_applications():
    email = request.args.get('email')
    password = request.args.get('password')
    
    user = User.query.filter_by(
        email=email,
        password=password,
        status=UserStatus.APPROVED
    ).first()
    
    if not user:
        return create_xml_response('error', {'message': 'Invalid credentials'}, 403)

    applications = Application.query.filter_by(user_id=user.id).all()
    
    root = ET.Element('applications')
    for app in applications:
        app_elem = ET.SubElement(root, 'application')
        job = Job.query.get(app.job_id)
        ET.SubElement(app_elem, 'id').text = str(app.id)
        ET.SubElement(app_elem, 'job_title').text = job.title
        ET.SubElement(app_elem, 'company').text = job.company
        ET.SubElement(app_elem, 'status').text = app.status.value

    xml_str = ET.tostring(root)
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Recruiter: Approve Application
@app.route('/applications/<int:application_id>/approve', methods=['PUT'])
def approve_application(application_id):
    email = request.form.get('email')
    password = request.form.get('password')
    
    recruiter = User.query.filter_by(
        email=email,
        password=password,
        role=UserRole.RECRUITER,
        status=UserStatus.APPROVED
    ).first()
    
    if not recruiter:
        return create_xml_response('error', {'message': 'Invalid recruiter credentials'}, 403)

    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    if job.recruiter_id != recruiter.id:
        return create_xml_response('error', {'message': 'Unauthorized'}, 403)

    application.status = ApplicationStatus.APPROVED
    db.session.commit()
    
    return create_xml_response('application', {
        'id': application.id,
        'status': application.status.value
    })

@app.route('/users/<int:user_id>/role', methods=['PUT'])
def change_role(user_id):
    admin_email = request.form.get('admin_email')
    new_role = request.form.get('role')
    
    admin = User.query.filter_by(
        email=admin_email,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED
    ).first()
    
    if not admin:
        return create_xml_response('error', {'message': 'Admin privileges required'}, 403)

    user = User.query.get_or_404(user_id)
    try:
        user.role = UserRole(new_role)
    except ValueError:
        abort(400)
        
    db.session.commit()
    return create_xml_response('user', {
        'id': user.id,
        'role': user.role.value
    })

# ... (keep other existing routes the same) ...

# --- INIT ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin only
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
        
        # Remove the sample job creation entirely
        # if not Job.query.first():
        #     ... (delete this block)
    app.run(debug=True)
