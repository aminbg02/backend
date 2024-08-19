import base64
import string
import random
import smtplib
import xmlrpc.client
from io import BytesIO
import re

import PyPDF2
from flask import Flask, jsonify, request
from flask_mail import Mail
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
import datetime
from flask_cors import CORS
import google.generativeai as palm
from pdfminer.high_level import extract_text

palm.configure(api_key="AIzaSyArdc2IgxbVsnaW2lQleyHCB4BVL6jfk1c")

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

        user_data = {'name': name, 'login': email, 'password': password, 'x_can_edit': False}
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
                                      {'fields': ['id','name', 'description','user_id']})

        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401

def find_job_by_id(jobs_list, job_id):
    for job in jobs_list:
        if job['id'] == job_id:
            return job
    return None

@app.post("/updatejob")
def updatejob( ):
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
    manager_id = int(request.json.get('manager_id'))
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id', 'name', 'description', 'user_id']})
        job = find_job_by_id(jobs_list, id)
        if isinstance(job['user_id'], list):
            print(job['user_id'][0])
        else:
            print("user_id is not a list")

        if job:
            if job['user_id'][0]== manager_id:  # Check if manager_id matches the user_id of the job
                job_id = job['id']
                models.execute_kw(db, uid, 'T', 'hr.job', 'unlink', [[id]])
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
    name = data.get('name')  # Name t3 Poste
    partner_name = data.get('partner_name')
    email = data.get('email')
    description = data.get('description')
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
            'description': description,
            'x_resume': encoded_file_data  # Assign the base64 encoded file data to the x_resume field
        }

        job_application_id = models.execute_kw(db, uid, 'T', 'hr.applicant', 'create', [job_application_data])

        if job_application_id:
            # Create the attachment record
            attachment_data = {
                'name': 'Resume.pdf',  # Name of the attachment
                'datas': encoded_file_data,  # Encoded file data
                'res_model': 'hr.applicant',
                'res_id': job_application_id,
                'type': 'binary',
            }

            attachment_id = models.execute_kw(db, uid, 'T', 'ir.attachment', 'create', [attachment_data])

            if attachment_id:
                return 'Application Successful'
            else:
                return 'Error creating attachment'
        else:
            return 'Error creating job application'

    return "Error"










def format_skills_text(skills_text):
    """
    Formats a string of skills and job descriptions into a more readable format.

    Args:
        skills_text (str): The input string to be formatted.

    Returns:
        str: The formatted string.
    """
    formatted_text = ""

    # Split the text into sections
    sections = skills_text.split("\n\n")

    # Format each section
    for section in sections:
        if section.startswith("- **"):
            # Skills section
            formatted_text += section.replace("- **", "## ").replace("- - ", "### ") + "\n\n"
        elif section.startswith("**Job "):
            # Job section
            formatted_text += section + "\n\n"
        else:
            # Other text
            formatted_text += section + "\n\n"

    return formatted_text


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
            
              "Some skills might be transferable,so consider if a candidate has the potenial to learn necessary skills for a particular opportunity ."
              "I look forward to your insights! mention the key skills they have that would fit in our company,  maximum 3 skills "
              "in your response, dont say is there a clear match for the ...., just say There is no clear match and so on, goes for all the 3 questions ")
    for job in jobs:
        if job['name']!="Chief Executive Officer" or job['name']!="Chief Technical Officer" :
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
    skills_formatted = skills
    print("***********************************************")
    print(format_skills_text(skills_formatted))
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
            'description': format_skills_text(skills_formatted),  # Use the generated skills
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
                                       {'fields': ['id', 'name', 'login','create_date','x_can_edit']})
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







@app.post('/get_response')
def get_response():
    url = 'http://localhost:8069'
    db = 'Test'
    user_query = request.json['user_query']
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'hr.job', 'search_read', [],
                                      {'fields': ['id', 'name', 'description']})

    job_details = ""
    for job in jobs_list:
        if len(job['name']) >= 6 and job['name'] != "Spontaneous Application":
            job_details += f"Position: {job['name']}\nDescription: {job['description']}\n\n"

    """
    Generates a response from the Palm model based on user query and company info.
    """

    info1="""Schedit & Bachman Maghreb  is  branch of a Schedit&Bachamnn multinational company. We're proud to be part of a large network with
     offices in many countries.We specialize in parking solutions, you can find us at     "3 Bis rue de la Teinturerie – Z.I. Sidi Rezig   

         
        
        NO MATTER WHAT,TRY TO BE AS SHORT AS POSSIBLE MAXIMUM 4 LINES"""
    palm.configure(api_key="AIzaSyArdc2IgxbVsnaW2lQleyHCB4BVL6jfk1c")

    # Select a suitable model
    models = [m for m in palm.list_models() if "generateText" in m.supported_generation_methods]
    model = models[0].name  # Replace with the desired model name

    # Combine user query and company information in the prompt
    prompt = (f" answer theUser's prompt : {user_query}\nconsidering this data , "
              f"but remebmer ,just give the necssary information in your answer, "
              f" and if the user asks anything that is not related about the company tell him you can not answer, "

              f"If someone wants some information about the company, give them a brief summary of the info i will give you!"
                f"If someone greets you, greet them back and ask them if they need any help , do not give information that are not asked of you"
               f"If someoneasks anything of you, be soo brief, as brief as possible"
              f"If someone mentions their skills and asks if there is an opprounity and in our company   there is not , tell them that now there is not but if there is an opportunity in the future it will be added to our update and keep checking "
              f"If someoneasks anything of you, be soo brief, as brief as possible"
         
              f"If someone says Thank you, say you're welcome, have a great day!"
            
              f"   Dont ever give informaiton unless asked of them"
              f" If someone asks in any language but english say i can only answer in english"
              f"     If you want to apply for a job, you can visit our website and apply through the jobs insterface, or you can just do a spontanoues applicaiton ( also be brief, just say go apply , and actually, eb brief in all of your answers, give necssary information and that is enough , also, if someone asks to list all the jobs , dont mention the spontanoues application"""
f"the answers must start with the first letter in upper case, formal answers"
              f"If there is no job matching IF they mentioned their skills between the user's skills and the job opportunities available right now, tell them to check regulary our website as any new job will be added there"


              )
    prompt = prompt + "here are information that you need to take into consideration!!" + info1
    prompt = prompt + "here are the jobs avaialble now!" + job_details


     # Generate text with Palm
    response = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0.3,  # Adjust for creativity
        max_output_tokens=800
    )

    return jsonify({'result': response.result})



@app.get("/test1_survery_question")
def test1():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.question', 'search_read', [],                                 )
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401






@app.get("/test2_surveyuser_inputline")
def test2():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.user_input.line', 'search_read', [])
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401



@app.get("/test3_survey_question_answer")
def test3():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.question.answer', 'search_read', [],)
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401



@app.get("/test4_survey_question_answer")
def test4():
    url = 'http://localhost:8069'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    question_id=request.json.get('question_id')

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.question.answer', 'search_read', [[['id', '=', question_id]]],)
        return jsonify(jobs_list)
    else:
        return jsonify({'message': 'Error while authenticating'}), 401




@app.post("/aaa")
def test34():
    url = 'http://localhost:8069/'
    db = 'Test'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, 'aminscbg@gmail.com', 'T', {})
    name = request.json.get("name")

    if uid:
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        domain = []  # Initialize an empty domain
        jobs_list = models.execute_kw(db, uid, 'T', 'survey.question', 'search_read', [domain],
                                      {'fields': ['suggested_answer_ids', 'survey_id', 'display_name']})

        results = []

        for record in jobs_list:
            if record['survey_id'][1] == name:
                question_data = {
                    "question": record["display_name"],
                    "answers": []
                }
                for q in record["suggested_answer_ids"]:
                    answers_list = models.execute_kw(db, uid, 'T', 'survey.question.answer', 'search_read',
                                                     [[['id', '=', q]]], {'fields': ['is_correct', 'value', ]})
                    for answer in answers_list:
                        question_data["answers"].append(answer)

                results.append(question_data)

        if results:
            return {"data": results}
        else:
            return {"message": 'No record found with survey_id matching "{}"'.format(name)}
    else:
        return {"message": 'Error while authenticating'}, 401



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