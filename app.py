import base64
import string
import random
import smtplib
import xmlrpc.client
from flask import Flask, jsonify, request
from flask_mail import Mail
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
import datetime
from flask_cors import CORS


app = Flask(__name__)
mail = Mail(app)
app.config['JWT_SECRET_KEY'] = 'code'  # Set a secret key for JWT signing
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})



@app.route('/emailtest')
def emailtest():
    email = "aminscbg@gmail.com"
    reciever = "benghorbelmohammedamin@gmail.com"
    subject = "password reset"
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(20))
    message = "your new password is " + password
    text = f"Subject: {subject}\n\n{message}"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, 'bpidtptxaukyabhm')
    server.sendmail(email, reciever, text)
    return "message sent"

@app.post("/login")
def login():
    url = 'http://localhost:8069'
    db = 'Test'
    email = request.json.get('email')
    password = request.json.get('password')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, email, password, {})

    if uid == 2:
        # Generate JWT token for admin user
        token_payload = {'email': email, 'role': 'admin', 'name': 'Admin',
                         'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800)}
        access_token = create_access_token(token_payload)
        return jsonify({'token': access_token})
    elif uid:
        # Generate JWT token for regular user
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_data = models.execute_kw(db, 2, 'T', 'res.users', 'search_read', [[['login', '=', email]]], {'fields': ['name']})
        if user_data:
            user_name = user_data[0]['name']
            token_payload = {'email': email, 'role': 'user', 'name': user_name,
                             'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800)}
            access_token = create_access_token(token_payload)
            return jsonify({'token': access_token})
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        url = 'http://localhost:8069'
        db = 'Test'
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
        if uid:
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            user_list = models.execute_kw(db, uid, 'T', 'res.users', 'search_read', [],
                                          {'fields': ['login', 'password']})
            for fetcher in user_list:
                if fetcher['login'] == email:
                    return jsonify({'message': 'Incorrect Password'}), 401
            return jsonify({'message': 'Incorrect Login'}), 401



@app.post("/signup")
def signup():
    url = 'http://localhost:8069'
    db = 'Test'
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_list = models.execute_kw(db, uid, 'T', 'res.users', 'search_read', [],
                                      {'fields': ['login', 'password']})
        for fetcher in user_list:
            if fetcher['login'] == email:
                return jsonify({'message': 'User already exists'}), 409

        user_data = {'name': name, 'login': email, 'password': password}
        iddd = models.execute_kw(db, uid, 'T', 'res.users', 'create', [user_data])

        if iddd:
            # Generate JWT token for the new user
            token_payload = {'email': email, 'role': 'user', 'name': name,
                             'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800)}
            access_token = create_access_token(token_payload)
            return jsonify({'token': access_token}), 201
        else:
            return jsonify({'message': 'Error while creating user'}), 500
    else:
        return jsonify({'message': 'Error while connecting'}), 500


@app.post("/addnewjob")
def addnewjob():
    url = 'http://localhost:8069'
    db = 'Test'
    name = request.json.get('name')
    description = request.json.get('description')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [], {'fields': ['name']})

        for job in jobs_list:
            if job['name'] == name:
                return jsonify({'message': 'Job already exists'}), 409

        job_description = {'name': name, 'description': description}
        job_id = models.execute_kw(db, uid, 'T', 'hr.job', 'create', [job_description])

        if job_id:
            return jsonify({'message': 'Job created'}), 201
        else:
            return jsonify({'message': 'Error while creating job'}), 500
    else:
        return jsonify({'message': 'Error while authenticating'}), 401




@app.get("/getalljobs")
def getjobdetails():
    url = 'http://localhost:8069'
    db = 'Test'
    #name = request.json.get('name')
    #description = request.json.get('description')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id','name', 'description']})
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401

def find_job_by_id(jobs_list, job_id):
    for job in jobs_list:
        if job['id'] == job_id:
            return job
    return None

@app.post("/updatejob")
def updatejob(  ):
    url = 'http://localhost:8069'
    db = 'Test'
    job_id = request.json.get('id')
    name = request.json.get('name')
    description = request.json.get('description')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [], {'fields': ['id', 'name', 'description']})
        job = find_job_by_id(jobs_list, job_id)
        if job:
            models.execute_kw(db, uid, 'T', 'hr.job', 'write', [[job_id], {'name': name, 'description': description}])
            return jsonify({'message': 'Job updated successfully'}), 200
        else:
            return jsonify({'message': 'Job not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401

@app.post("/deletejob")
def deletejob():
    url = 'http://localhost:8069'
    db = 'Test'
    id = request.json.get('id')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [], {'fields': ['id', 'name', 'description']})
        job = find_job_by_id(jobs_list, id)
        if job:
            job_id = job['id']
            models.execute_kw(db, uid, 'T', 'hr.job', 'unlink', [[job_id]])
            remaining_jobs = models.execute_kw(db, uid, 'T', 'hr.job', 'search', [[['id', '=', job_id]]])
            if not remaining_jobs:
                return jsonify({'message': 'Deletion successful'}), 200
            else:
                return jsonify({'message': 'Error while deleting job'}), 500
        else:
            return jsonify({'message': 'Job not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401


@app.get("/getjob/<jid>")
def get_job_detail(jid):
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id', 'name', 'description']})
        for item in jobs_list:
            if str(item['id'])==str(jid):
                return item
        return "job doesnt exist"
    else:
        return "error in connection"


@app.get("/applicants/<int:job_id>")
def get_job_applicants(job_id):
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        # Search for applicants for the specified job ID
        if job_id == 37:
            applicant_ids = models.execute_kw(db, uid, 'T', 'hr.applicant', 'search_read',
                                              [[('name', '=', "Spontaneous Application")]],
                                              {'fields': ['name', 'partner_name', 'email_from', 'x_resume',
                                                          'x_skills_list']})
        else:
            applicant_ids = models.execute_kw(db, uid, 'T', 'hr.applicant', 'search_read',
                                              [[('id', '=', job_id)]],
                                              {'fields': ['name', 'partner_name', 'email_from', 'x_resume']})

        if applicant_ids:
            applicants_data = []
            for applicant in applicant_ids:
                applicant_data = {
                    'name': applicant.get('name'),
                    'email': applicant.get('email_from'),
                }

                if applicant.get('name') == "Spontaneous Application":
                    applicant_data['x_skills_list'] = applicant.get('x_skills_list')

                applicants_data.append(applicant_data)

            return jsonify({'applicants': applicants_data})
        else:
            return "No applicants found for this job ID"

    return "Error"


@app.post("/applyforjob")
def applyforjob():
    url = 'http://localhost:8069'
    db = 'Test'
    data = request.form
    name = data.get('name') #Name t3 Poste
    partner_name = data.get('partner_name')
    email = data.get('email')
    job_id = int(data.get('job_id'))
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        # Check if an application with the same email already exists
        existing_application_ids = models.execute_kw(db, uid, 'T', 'hr.applicant', 'search',
                                                      [[('email_from', '=', email)]])
        if existing_application_ids:
            return "An application with this email already exists"
        # Read the PDF file as binary data
        pdf_file = request.files['pdf_file']
        file_data = pdf_file.read()

        # Encode the file data as base64
        encoded_file_data = base64.b64encode(file_data).decode('utf-8')

        # Create a dictionary with job application data including the base64 encoded PDF file
        job_application_data = {
            'name': name,
            'partner_name': partner_name,
            'email_from': email,
            'job_id': job_id,
            'description': "PDF File Attached",
            'x_resume': encoded_file_data  # Assign the base64 encoded file data to the x_resume field
        }

        job_application_id = models.execute_kw(db, uid, 'T', 'hr.applicant', 'create', [job_application_data])

        if job_application_id:
            return "Application Successful"

    return "Error"

@app.post("/spontaneousapplication")
def spontaneous_application():
    url = 'http://localhost:8069'
    db = 'Test'
    data = request.form
    partner_name= data.get('partner_name')
    email = data.get('email')
    skills_list=data.get('skills_list')
    pdf_file = request.files['pdf_file']
    file_data = pdf_file.read()
    encoded_file_data = base64.b64encode(file_data).decode('utf-8')

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        # Check if an application with the same email already exists
        existing_application_ids = models.execute_kw(db, uid, 'T', 'hr.applicant', 'search',
                                                      [[('email_from', '=', email)]])
        if existing_application_ids:
            return "An application with this email already exists"

        # Read the PDF file as binary data

        # Create a dictionary with job application data including the base64 encoded PDF file
        job_application_data = {
            'name': "Spontaneous Application",
            'partner_name': partner_name,
            'email_from': email,
            'job_id': 37,
            'description': "PDF File Attached",
            'x_resume': encoded_file_data ,
            'x_skills_list':skills_list
        }
        job_application_id = models.execute_kw(db, uid, 'T', 'hr.applicant', 'create', [job_application_data])
        if job_application_id:
            return "Application Successful"
    return "Error"



@app.post("/changepassword")
def changepw():
    url = 'http://localhost:8069'
    db = 'Test'
    email = request.json.get('email')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_list = models.execute_kw(db, uid, 'T', 'res.users', 'search_read', [], {'fields': ['id', 'login', 'password']})
        user_found = False
        for user in user_list:
            if user['login'] == email:
                user_found = True
                current_id = user['id']
                break
        if user_found:
            sender_email = "aminscbg@gmail.com"
            receiver_email = email
            subject = "Password reset"
            characters = string.ascii_letters + string.digits + string.punctuation
            new_password = ''.join(random.choice(characters) for _ in range(20))
            message = f"Your new password is {new_password}"
            text = f"Subject: {subject}\n\n{message}"
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender_email, 'bpidtptxaukyabhm')
                server.sendmail(sender_email, receiver_email, text)
                models.execute_kw(db, uid, 'T', 'res.users', 'write', [[current_id], {'password': new_password}])
                return jsonify({'message': 'Password changed successfully'}), 200
            except Exception as e:
                return jsonify({'message': 'Error while sending email'}), 500
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401



#tomake
#@app.get("/applicationsmadebyuser/<int:job_id>")