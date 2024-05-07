import base64
import string
import random
import smtplib
import xmlrpc.client
import PyPDF2
from flask import Flask, jsonify, request
from flask_mail import Mail
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
import datetime
from flask_cors import CORS, cross_origin
import google.generativeai as palm
palm.configure(api_key="AIzaSyArdc2IgxbVsnaW2lQleyHCB4BVL6jfk1c")
app = Flask(__name__)
mail = Mail(app)

jwt = JWTManager(app)
CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})
CORS(app, resources={r"/*": {"origins": "http://localhost:4200/jobs"}})



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
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_data = models.execute_kw(db, 2, 'T', 'res.users', 'search_read', [[['login', '=', email]]], {'fields': ['id', 'name']})
        if user_data:
            user_name = user_data[0]['name']
            user_id = user_data[0]['id']
            token_payload = {
                'email': email,
                'role': 'admin',
                'name': user_name,
                'user_id': user_id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800)
            }
            access_token = create_access_token(token_payload)
            return jsonify({'token': access_token})
        else:
            return jsonify({'message': 'User not found'}), 404
    elif uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_data = models.execute_kw(db, 2, 'T', 'res.users', 'search_read', [[['login', '=', email]]], {'fields': ['name']})
        if user_data:
            user_name = user_data[0]['name']
            user_id = user_data[0]['id']
            token_payload = {
                'email': email,
                'role': 'user',
                'name': user_name,
                'user_id': user_id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800)
            }
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
            token_payload = {'email': email, 'role': 'user', 'name': name, 'id':iddd,
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
    manager_id =request.json.get('id')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [], {'fields': ['name']})

        for job in jobs_list:
            if job['name'] == name:
                return jsonify({'message': 'Job already exists'}), 409

        job_description = {'name': name, 'description': description ,'user_id':manager_id}
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
def updatejob():
    url = 'http://localhost:8069'
    db = 'Test'
    job_id = request.json.get('id')
    name = request.json.get('name')
    manager_id = int(request.json.get('manager_id'))
    description = request.json.get('description')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id', 'name', 'description', 'user_id']})
        job = find_job_by_id(jobs_list, job_id)

        if job:
            if job['user_id'][0] == manager_id:  # Check if manager_id matches the user_id of the job
                models.execute_kw(db, uid, 'T', 'hr.job', 'write',
                                  [[job_id], {'name': name, 'description': description}])
                return jsonify({'message': 'Job updated successfully'}), 200
            else:
                return jsonify({'message': 'Unauthorized to update this job'}), 403
        else:
            return jsonify({'message': 'Job not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401


@app.post("/deletejob")
def deletejob():
    url = 'http://localhost:8069'
    db = 'Test'
    id = request.json.get('id')
    manager_id = int(request.json.get('manager_id'))
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],

                                      {'fields': ['id', 'name', 'description', 'user_id']})
        job = find_job_by_id(jobs_list, id)

        if job:
            if job['user_id'][0] == manager_id:  # Check if manager_id matches the user_id of the job
                job_id = job['id']
                models.execute_kw(db, uid, 'T', 'hr.job', 'unlink', [[job_id]])
                remaining_jobs = models.execute_kw(db, uid, 'T', 'hr.job', 'search', [[['id', '=', job_id]]])

                if not remaining_jobs:
                    return jsonify({'message': 'Deletion successful'}), 200
                else:
                    return jsonify({'message': 'Error while deleting job'}), 500
            else:
                return jsonify({'message': 'Unauthorized to delete this job'}), 403
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


        #rech app selon job id
        if job_id == 9:
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


@app.post('/applyforjob')
def applyforjob():
    url = 'http://localhost:8069'
    db = 'Test'
    data = request.form
    name = data.get('name')  # Name t3 Poste , remember to send the appropaite name in the frontend part
    partner_name = data.get('partner_name')  # esm appliacnt
    email = data.get('email')
    job_id = int(data.get('job_id'))
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
            return 'An application with this email already exists'

        # Create the applicant record
        job_application_data = {
            'name': name,  # Name of the job position
            'partner_name': partner_name,
            'email_from': email,
            'job_id': job_id,
        }
        applicant_id = models.execute_kw(db, uid, 'T', 'hr.applicant', 'create', [job_application_data])

        # Create the attachment record
        attachment_data = {
            'name': 'Resume.pdf',  # Name of the attachment
            'datas': encoded_file_data,  # Encoded file data
            'res_model': 'hr.applicant',
            'res_id': applicant_id,
            'type': 'binary',
        }
        attachment_id = models.execute_kw(db, uid, 'T', 'ir.attachment', 'create', [attachment_data])

        if attachment_id:
            return 'Application Successful'

    return 'Error2'

import google.generativeai as palm
import xmlrpc.client
import base64
from flask import Flask, request, jsonify
import re
from pdfminer.high_level import extract_text
from io import BytesIO

app = Flask(__name__)

@app.get("/getalljobs")
def getjobdetails():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id', 'name', 'description']})
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401

@app.post("/spontaneousapplication")
def spontaneous_application():
    url = 'http://localhost:8069'
    db = 'Test'
    data = request.form
    name = data.get('name')  # Name t3 Poste , remember to send the appropaite name in the frontend part
    name = "Spontaneous Application"
    partner_name = data.get('partner_name')  # esm appliacnt
    email = data.get('email')
    pdf_file = request.files['pdf_file']
    # Get all job details
    jobs_response = getjobdetails()
    jobs = jobs_response.json
    # Read the content of the PDF file
    pdf_content = pdf_file.read()
    # Extract text from the PDF content
    text = extract_text(BytesIO(pdf_content))
    pattern = re.compile("[a-zA-Z]+")
    matches = pattern.findall(text)
    # Construct the prompt with job opportunities and descriptions
    prompt = ("Hey Sam, I have Analyzed a candidate's resume and extracted the following list of skills and experiecne " +
              ', '.join(matches) + "Based on these qualifications, let us see if there is s a potential match among the  job opportunities that will be mentioned at the end of this messages:  "
                " "+
              "Before we delve into the analysis , can you also determine if the resume text is in french and treat it accordingly ?That will help us in the evaluation."
                    "Now lets us proceed with your insights : "
              "1 If there is a clear match for the candidate in any of these job opportunities? if so, which one and why? "
              "2 If there is no perfect match, which opportunity might be the closes fit based on the skills of the candidate and experience? Explain your reasoning."
              "3 Considering the qualifications of the candidate, what job title or area do you think they would be most successful in ,even if its not directly listed here?"
              "Please note: "
              "-This is just a general overview of their skills . A more comprehensive evaluation may be necssary for a final decision."
              "Some skills might be transferable,so consider if a candidate has the potenial to learn necessary skills for a particular opportunity ."
              "I look forward to your insights! also, please at the start of the response, mention what are their skills, like a brief summary about the projects if there is any too ( please be as brief as you can , dont go over 600 characters) ")
    for job in jobs:
        prompt += f"Position: {job['name']}\nDescription: {job['description']}\n\n"

    palm.configure(api_key="AIzaSyArdc2IgxbVsnaW2lQleyHCB4BVL6jfk1c")
    models = [m for m in palm.list_models() if "generateText" in m.supported_generation_methods]
    for m in models:
        print(m.name)
    model = models[0].name

    com = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0.3,
        max_output_tokens=800,
    )

    # Store the generated text in the 'skills' variable
    skills = com.result.strip()
    skills_formatted = "- " + "\n- ".join(skills.split("\n"))
    encoded_file_data = base64.b64encode(pdf_content).decode('utf-8')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        print(matches)
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        # Check if an application with the same email already exists
        existing_application_ids = models.execute_kw(db, uid, 'T', 'hr.applicant', 'search',
                                                     [[('email_from', '=', email)]])
        if existing_application_ids:
            return 'An application with this email already exists'

        # Create the applicant record
        job_application_data = {
            'name': name,  # Name of the job position
            'partner_name': partner_name,
            'email_from': email,
            'description': skills_formatted,  # Use the generated skills
            'job_id': 9,
        }
        applicant_id = models.execute_kw(db, uid, 'T', 'hr.applicant', 'create', [job_application_data])

        # Create the attachment record
        attachment_data = {
            'name': 'Resume.pdf',  # Name of the attachment
            'datas': encoded_file_data,  # Encoded file data
            'res_model': 'hr.applicant',
            'res_id': applicant_id,
            'type': 'binary',
        }
        attachment_id = models.execute_kw(db, uid, 'T', 'ir.attachment', 'create', [attachment_data])

        if attachment_id:
            return 'Application Successful'

    return 'Error2'


@app.post("/changepassword2")
def changepw2():
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

@app.post("/changepassword")
@cross_origin(origins='http://localhost:4200')

def changepw():
    url = 'http://localhost:8069'
    db = 'Test'
    email = request.json.get('email')
    new_password = request.json.get('new_password')
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
            try:
                models.execute_kw(db, uid, 'T', 'res.users', 'write', [[current_id], {'password': new_password}])
                return jsonify({'message': 'Password changed successfully'}), 200
            except Exception as e:
                return jsonify({'message': 'Error while changing password0'}), 500
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401


@app.post("/change_email")
def change_email():
    url = 'http://localhost:8069'
    db = 'Test'
    old_email = request.json.get('old_email')
    new_email = request.json.get('new_email')

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_id = models.execute_kw(db, uid, 'T', 'res.users', 'search', [[('login', '=', old_email)]])

        if user_id:
            try:
                models.execute_kw(db, uid, 'T', 'res.users', 'write', [user_id, {'login': new_email}])
                return jsonify({'message': 'Email changed successfully'}), 200
            except Exception as e:
                return jsonify({'message': 'Error while changing email'}), 500
        else:
            return jsonify({'message': 'User not found'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401


@app.post("/changename")
def change_name():
    url = 'http://localhost:8069'
    db = 'Test'
    email = request.json.get("email")  # Now used to identify the user
    new_name = request.json.get('new_name')

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        user_id = models.execute_kw(db, uid, 'T', 'res.users', 'search', [[('login', '=', email)]])

        if user_id:
            try:
                models.execute_kw(db, uid, 'T', 'res.users', 'write', [user_id, {'name': new_name}])
                return jsonify({'message': 'Name changed successfully'}), 200
            except Exception as e:
                return jsonify({'message': 'Error while changing name'}), 500
        else:
            return jsonify({'message': 'User not found 55'}), 404
    else:
        return jsonify({'message': 'Error while authenticating'}), 401



@app.post('/send_email')
def send_email():
    name = "COTNACT FROM WEBSITE"
    email = request.json.get('email')
    subject = request.json.get('subject')
    message = request.json.get('message') +"   " +email

    # Configure email settings
    sender_email = email
    receiver_email = 'aminscbg@gmail.com' #this changes to whatever the email of the receiver of each email
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'aminscbg@gmail.com'
    smtp_password = 'bpidtptxaukyabhm'

    email_content = f"From: {name} <{sender_email}>\nSubject: {subject}\n\n{message}"

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, email_content)
        server.quit()
        return jsonify({'message': 'Email sent successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
#tomake
#@app.get("/applicationsmadebyuser/<int:job_id>")





@app.post("/pdf")
def managepdf():
    url = 'http://localhost:8069'
    pdf_file = request.files['file']
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    text = ""
    for page_num in range(pdf_reader.numPages):
        page_obj = pdf_reader.getPage(page_num)
        text += page_obj.extractText()
    return text



@app.post("/deleteuser")
def delete_user():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    user_id = int(request.json.get('user_id'))

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        if user_id:
            try:
                models.execute_kw(db, uid, 'T', 'res.users', 'unlink', [user_id])
                return jsonify({'message': 'User deleted successfully'}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 500
        else:
            return jsonify({'message': 'User with this ID does not exist in  '}), 400
    else:
        return jsonify({'message': 'Error while authenticating'}), 401
@app.get("/getallusers")
def get_all_users():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        users_list = models.execute_kw(db, uid, 'T', 'res.users', 'search_read', [],
                                       {'fields': ['id', 'name', 'login']})
        return jsonify(users_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401


@app.post('/addnewuser')
def add_user():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    name = request.json.get('name')
    email = request.json.get('email')
    password = request.json.get('password')

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
            return jsonify({'message': "user created!"}), 201
        else:
            return jsonify({'message': 'Error while creating user'}), 500
    else:
        return jsonify({'message': 'Error while authenticating'}), 401
















@app.get("/gett")
def gett():
    url = 'http://localhost:8069'
    db = 'Test'
    #name = request.json.get('name')
    #description = request.json.get('description')
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.question', 'search_read', [[('title', '=', "is angular a frontend or backend framework")]],
                                      )


        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401







info = """
Scheidt & Bachmann Maghreeb, a family business founded in 1872, is presently led by Dr.-Ing. Norbert Miller, representing the fifth generation of family shareholders. With a workforce of approximately 3,300 individuals from nearly 50 nations, we are dedicated to crafting innovative solutions for a dynamic world. Our focus extends beyond mere provision of barriers and machines; the crux lies in the intelligence and integration of our system solutions. Software development and service management form the core of our offerings, driving predictive, intelligent mobility solutions.

Our enduring success hinges on one simple principle: belief in the capabilities of our employees. We are committed to delivering products, developments, and services of unparalleled quality to our customers, underpinned by our shared company values.

These values are ingrained in our corporate culture and guide our interactions with employees, colleagues, customers, suppliers, and partners. Respect forms the cornerstone of our operations. As a socially responsible entity, we strive to harmonize business needs with employee interests, while also upholding environmental sustainability.

Trust and personal responsibility are paramount in our philosophy. We place faith in the competence and potential of our team members, fostering an environment of mutual trust and accountability. Our commitment to continuous improvement fosters an atmosphere of learning and growth, where mistakes are viewed as opportunities for development.

Team spirit and passion drive us towards collective success. We operate as a cohesive unit, supporting one another and celebrating shared achievements. Our goals, rooted in profitable growth and sustainable management, reflect our dedication to employee satisfaction, customer orientation, innovation, international expansion, and career development.

For professionals like you, Scheidt & Bachmann offers a platform to leverage your expertise and contribute to our shared vision. Through initiatives like the #JUMP management program and lifelong learning opportunities, we encourage personal and professional development, ensuring that you reach your full potential while shaping the future of mobility with us. Join us, and together, let's redefine the boundaries of possibility in software engineering and beyond.
"""

palm.configure(api_key="AIzaSyArdc2IgxbVsnaW2lQleyHCB4BVL6jfk1c")
models = [m for m in palm.list_models() if "generateText" in m.supported_generation_methods]
model = models[0].name  # Replace with the desired model name

@app.post('/get_response')
def get_response():
    """
    Generates a response from the Palm model based on user query and company info.
    """
    user_query = request.json['user_query']

    # Combine user query and company information in the prompt
    prompt = (f" answer theUser's prompt : {user_query}\nconsidering this data , "
              f"but remebmer ,just give the necssary information in your answer, "
              f" and if the user asks anything that is not related about the company , "
              f"just say that you are unable to answer as you are only capable to give info about the company{info}\nAssistant:")

    # Generate text with Palm
    response = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0.3,  # Adjust for creativity
        max_output_tokens=800
    )

    return jsonify({'result': response.result})




