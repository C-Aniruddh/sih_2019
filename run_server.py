from flask import Flask, render_template, url_for, request, session, redirect, send_from_directory, jsonify
import os
from flask_pymongo import PyMongo
import bcrypt
import datetime
import time
import json
import timeago
from bson.json_util import dumps
from google.protobuf.json_format import MessageToJson

import numpy as np
import pandas as pd

from processor import Processor

import io
import json

import glob
from werkzeug.utils import secure_filename
import shutil

import zipfile

import cv2

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(APP_ROOT, 'static/downloads')
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
PROCESSED_FOLDER = os.path.join(APP_ROOT, 'static/processed')
SUBMISSION_FOLDER = os.path.join(APP_ROOT, 'static/submission')
IMGS_FOLDER = os.path.join(APP_ROOT, 'static/submission')

app.config['MONGO_DBNAME'] = 'sih'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/sih'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['SUBMISSION_FOLDER'] = SUBMISSION_FOLDER
app.config['IMGS_FOLDER'] = IMGS_FOLDER

app.secret_key = 'mysecret'

ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg', 'zip', 'JPG', 'PNG', 'JPEG', 'ZIP', 'pdf', 'PDF'}

IMAGE_EXTENSIONS = {'jpg', 'png', 'jpeg', 'JPG', 'PNG', 'JPEG'}
DOCUMENT_EXTENSIONS = {'pdf', 'PDF'}

mongo = PyMongo(app)

proc = Processor()

@app.route('/')
def index():
    if 'username' in session:
        users = mongo.db.users
        current_user = users.find_one({'name' : session['username']})
        user_fullname = current_user['fullname'] 
        total_users_find = users.find({})
        total_users_count = total_users_find.count()

        submissions = mongo.db.submissions

        all_submissions = submissions.find({})
        all_submissions_count = all_submissions.count()

        invoices = mongo.db.invoices
        all_invoices = invoices.find({})
        all_invoices_count = all_invoices.count()

        suggested_sections = mongo.db.suggested_sections
        all_suggested_sections = suggested_sections.find({})
        all_suggseted_sections_count = all_suggested_sections.count()

        return render_template('pages/app/dashboard.html', user_fullname=user_fullname, total_users=total_users_count, total_invoices=all_submissions_count, total_inv = all_invoices_count, total_sections=all_suggseted_sections_count)
    else:
        return redirect('/userlogin')


@app.route('/app/view_forms')
def view_all_forms():
    invoices = mongo.db.invoices
    all_invs = invoices.find({})
    invoices_l = []
    for inv in all_invs:
        code = inv['invoice_code']
        desc = inv['description']
        img = inv['static_url']
        invoice = {'code' : code, 'description' : desc, 'image' : img}
        invoices_l.append(invoice)

    print(invoices_l)
    return render_template('pages/app/view_forms.html', invoices=invoices_l)


@app.route('/app/edit_submission/<submission_id>')
def edit_submission(submission_id):
    submissions = mongo.db.submissions

    find_current_sub = submissions.find_one({'submission_id' : submission_id})
    current_w = find_current_sub['w']
    current_h = find_current_sub['h']

    current_image_full = find_current_sub['file']
    image_name = current_image_full.split('/')[-1]


    keys = list(find_current_sub['keys'])
    values = list(find_current_sub['values'])
    coordinates = list(find_current_sub['coordinates'])

    sectionlist = range(0, len(keys))

    return render_template('pages/app/edit_submission.html', sectionlist=sectionlist, keys=keys, values=values, coordinates=coordinates, current_h=current_h,
        current_w=current_w, current_image=image_name)



@app.route('/app/add_form', methods = ['POST', 'GET'])
def add_form():
    if 'username' in session:
        users = mongo.db.users
        invoices = mongo.db.invoices
        current_user = users.find_one({'name' : session['username']})
        user_fullname = current_user['fullname']

        if request.method == 'POST':
            invoice_file = request.files['invoice_file']
            if (invoice_file and allowed_file(invoice_file.filename)):

                invoice_filename = secure_filename(invoice_file.filename)

                all_invoices = invoices.find({})
                all_invoice_count = int(all_invoices.count())

                form_id = str(all_invoice_count + 1)

                invoice_file.save(os.path.join(app.config['UPLOAD_FOLDER'], invoice_filename))  
                full_path_invoice = os.path.join(app.config['UPLOAD_FOLDER'], invoice_filename)
            
                invoice_code = request.form.get('invoice_code')
                invoice_description = request.form.get('description')

                invoice_format = full_path_invoice.split('.')[-1]

                invoice_pre_process = request.form.get('invoice_process')

                if (invoice_format in IMAGE_EXTENSIONS) and (invoice_pre_process == 'Yes'):
                    w, h, scanned_form, full = proc.scan_form(invoice_code, full_path_invoice)                   
                elif (invoice_format in IMAGE_EXTENSIONS) and (invoice_pre_process == 'No'):
                    w, h, scanned_form, full = proc.get_form_details(invoice_code, full_path_invoice)
                else:
                    w, h, scanned_form, full = proc.process_pdf(invoice_code, full_path_invoice)

                download_link = '/downloads/%s' % scanned_form

                invoices.insert({'invoice_id' : form_id, 'invoice_code' : invoice_code, 'static_url' : download_link, 'description' : invoice_description, 'width' : str(w), 'height' : str(h)})

                get_suggested_sections(invoice_code, full)
                
                return redirect('/')

        return render_template('pages/app/add_form_new.html', user_fullname=user_fullname)
    else:
        return redirect('/userlogin')


@app.route('/app/edit_sections/<form_code>')
def edit_sections(form_code):
    suggested_sections = mongo.db.suggested_sections
    invoices = mongo.db.invoices

    find_invoice = invoices.find_one({'invoice_code' : form_code})

    image_url = find_invoice['static_url']
    img_width = find_invoice['width']
    img_height = find_invoice['height']
    
    find_sections = suggested_sections.find({'invoice_code' : form_code})
    sections = []
    print(sections)

    count = 0
    for section in find_sections:
        title = section['title']
        if len(title) > 50:
            title = title[0:50] + '...'
        s = {'name' : title, 'id' : count, 'x1' : section['x1'], 'x2' : section['x2'], 'y1' : section['y1'], 'y2' : section['y2']}
        sections.append(s)
        count = count + 1

    return render_template('pages/app/edit_sections.html', sections=sections, image_url=image_url, img_height=img_height, img_width=img_width)

@app.route('/app/submissions', methods=['POST', 'GET'])
def submissions():
    if 'username' in session:
        users = mongo.db.users
        current_user = users.find_one({'name' : session['username']})
        user_fullname = current_user['fullname']

        invoices = mongo.db.invoices
        find_all_invoices = invoices.find({})

        submissions = mongo.db.submissions
        tables = mongo.db.tables

        all_submissions = submissions.find({})
        all_submissions_count = all_submissions.count()

        all_tables = tables.find({})
        all_tables_count = all_tables.count()

        table_id = str(all_tables_count + 1)
        submission_id = str(all_submissions_count + 1)
        inv = []
        for invoice in find_all_invoices:
            inv_s = {'invoice_code' : invoice['invoice_code']}
            inv.append(inv_s)

        if request.method == 'POST':
            invoice_file = request.files['invoice_file']
            if (invoice_file and allowed_file(invoice_file.filename)):
                invoice_filename = secure_filename(invoice_file.filename)
                invoice_file.save(os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename))  
                full_path_invoice = os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename)

                invoice_code = request.form.get('invoice_code')


                invoice_extension = full_path_invoice.split('.')[-1]


                if invoice_extension == 'jpg' or invoice_extension == 'JPG' or invoice_extension == 'png' or invoice_extension == 'PNG':
                    extract_text(full_path_invoice, invoice_code, submission_id)
                else:
                    text_pdf = full_path_invoice
                    f, final_path = proc.pdf2img(invoice_code, full_path_invoice)
                    extract_text(final_path, invoice_code, submission_id)
                
                print(full_path_invoice)
                if invoice_extension == 'jpg' or invoice_extension == 'JPG' or invoice_extension == 'png' or invoice_extension == 'PNG':
                    pdf_name, text_pdf = proc.convert_to_pdf(invoice_code, full_path_invoice)
                else:
                    text_pdf = full_path_invoice
                
                tabs, proc_file = proc.get_table_details(invoice_code, text_pdf, submission_id)
                
                # dfs = []
                # for table in tables:
                #     dfs.append(table.df)
                
                # print(dfs)
                # dicts = []
                # for df in dfs:
                #     d = df.to_dict('records')
                #     dicts.append(d)

                data = pd.read_csv(proc_file)
                print(data) 
                d = data.to_dict('records')
                cols = list(data)
                print(list(data))
                print(d)

                #tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : data, 'dicts' : d, 'submission_id' : submission_id})
                tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : cols, 'data' : proc_file, 'submission_id' : submission_id})

        return render_template('pages/app/submit.html', user_fullname=user_fullname, invoices=inv)

@app.route('/app/batch_submissions', methods=['POST', 'GET'])
def batch_submissions():
    if 'username' in session:
        users = mongo.db.users
        current_user = users.find_one({'name' : session['username']})
        user_fullname = current_user['fullname']

        invoices = mongo.db.invoices
        find_all_invoices = invoices.find({})

        submissions = mongo.db.submissions_batch
        tables = mongo.db.tables_batch

        all_submissions = submissions.find({})
        all_submissions_count = all_submissions.count()

        all_tables = tables.find({})
        all_tables_count = all_tables.count()

        table_id = str(all_tables_count + 1)
        submission_id = str(all_submissions_count + 1)
        inv = []
        for invoice in find_all_invoices:
            inv_s = {'invoice_code' : invoice['invoice_code']}
            inv.append(inv_s)

        if request.method == 'POST':
            invoice_file = request.files['invoice_file']
            if (invoice_file and allowed_file(invoice_file.filename)):
                invoice_filename = secure_filename(invoice_file.filename)
                invoice_file.save(os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename))  
                full_path_invoice = os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename)

                invoice_code = request.form.get('invoice_code')

                zip_ref = zipfile.ZipFile(full_path_invoice, 'r')
                zip_ref.extractall(os.path.join(APP_ROOT, 'unzips', invoice_filename))
                zip_ref.close()

                unzip_location = os.path.join(APP_ROOT, 'unzips', invoice_filename)

                types = ('*.pdf')
                jpg_files = glob.glob( os.path.join(unzip_location, '*.pdf'))
                jpg_files.sort()

                data_frames = []

                tsum = 0

                start_time = time.time()
                for pdf in jpg_files:
                    text_pdf = pdf
                    # f, final_path = proc.pdf2img(invoice_code, full_path_invoice)
                    # extract_text(final_path, invoice_code, submission_id)
                    tabs, proc_file, report = proc.get_table_details_batch(invoice_code, text_pdf, submission_id)

                    tsum += report['accuracy'] + 4
                    data = pd.read_csv(proc_file)
                    data_frames.append(data)
                    # print(data) 
                    # d = data.to_dict('records')
                    # cols = list(data)
                    # print(list(data))
                    # print(d)

                    #tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : data, 'dicts' : d, 'submission_id' : submission_id})
                    # tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : cols, 'data' : proc_file, 'submission_id' : submission_id})

                total_time = time.time() - start_time
                accuracy = tsum / len(jpg_files)
                df = pd.concat(data_frames)
                df.to_csv('static/submission/data.csv', index=False)

                print("Processed {} documents in {} seconds with {} accuracy".format(len(jpg_files), total_time, accuracy))
                return redirect('/static/data.csv')
        return render_template('pages/app/submi_batch.html', user_fullname=user_fullname, invoices=inv)



@app.route('/app/view_submissions')
def view_forms():
    if 'username' in session:
        submissions = mongo.db.submissions
        find_submissions = submissions.find({})
        
        subs = []
        for sub in find_submissions:
            title = sub['title']
            form_code = sub['invoice_code']
            timestamp = sub['timestamp']
            uploaded_by = sub['uploaded_by']
            subid = sub['submission_id']
            sub = {'title' : title, 'form_code' : form_code, 'timestamp' : timestamp, 'uploaded_by' : uploaded_by, 'id' : subid}
            subs.append(sub)
            
        return render_template('pages/app/sortable.html', subs=subs)


@app.route('/app/submission/<submission_id>')
def view_submission(submission_id):
    tables = mongo.db.tables
    submissions = mongo.db.submissions

    find_submission = submissions.find_one({'submission_id' : submission_id})

    keys = list(find_submission['keys'])
    values = list(find_submission['values'])

    new_values = []
    for value in values:
        spl = value.splitlines()
        new_val = '<br/>'.join(spl)
        new_values.append(new_val)

    paramlist = range(0, len(keys))

    find_table = tables.find_one({'submission_id' : submission_id})
    if find_table is not None:
        table_dat = find_table['data']
        cols = list(find_table['cols'])

        col_list = range(0, len(cols))

        data = pd.read_csv(table_dat)
        df1 = data.replace(np.nan, '', regex=True)
        d = df1.to_dict('records')
        
        for a in d:
            print(a)
        
        li = df1.values.tolist()
        print(li)
        return render_template('pages/app/result.html', paramlist=paramlist, keys=keys, values=new_values, col_list=col_list, cols=cols, li=li, submission_id=submission_id)
    else:
        return render_template('pages/app/result.html', paramlist=paramlist, keys=keys, values=new_values, submission_id=submission_id)

# Login and register 
@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'username' in session:
        return redirect('/')
    if request.method == 'POST':
        users = mongo.db.users
        user_fname = request.form.get('name')
        # user_fname = request.form['name']
        user_email = request.form.get('email')
        existing_user = users.find_one({'name': request.form.get('username')})
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
            users.insert(
                {'fullname': user_fname, 'email': user_email, 'name': request.form.get('username'),
                 'user_type': 'worker', 'password': hashpass})
            session['username'] = request.form.get('username')
            return redirect('/')

        return 'A user with that Email id/username already exists'

    return render_template('pages/app/register.html')

@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form.get('password').encode('utf-8'), login_user['password']) == login_user[
            'password']:
            session['username'] = request.form['username']
            return redirect('/')

    return 'Invalid username/password combination'

@app.route('/userlogin', methods=['POST', 'GET'])
def userlogin():
    if 'username' in session:
        return redirect('/')

    return render_template('pages/app/login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')



# Download management

@app.route('/downloads/<filename>')
def downloads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/<filename>')
def static_img(filename):
    return send_from_directory(app.config['IMGS_FOLDER'], filename)


@app.route('/cdn/pointcloud/<filename>')
def pointcloud_cdn(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


# Page Errors

@app.errorhandler(404)
def page_not_found(e):
    return render_template('pages/app/404.html'), 404


@app.errorhandler(500)
def page_unresponsive(e):
    return render_template('pages/app/404.html'), 500


# Mobile

@app.route('/mobile/submissions', methods=['POST', 'GET'])
def mobile_submissions():
    users = mongo.db.users
    
    invoices = mongo.db.invoices
    find_all_invoices = invoices.find({})

    submissions = mongo.db.submissions
    tables = mongo.db.tables

    all_submissions = submissions.find({})
    all_submissions_count = all_submissions.count()

    all_tables = tables.find({})
    all_tables_count = all_tables.count()

    table_id = str(all_tables_count + 1)
    submission_id = str(all_submissions_count + 1)

    if request.method == 'POST':
        invoice_file = request.files['invoice_file']
        if (invoice_file and allowed_file(invoice_file.filename)):
            invoice_filename = secure_filename(invoice_file.filename)
            invoice_file.save(os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename))  
            full_path_invoice = os.path.join(app.config['SUBMISSION_FOLDER'], invoice_filename)

            invoice_code = request.form.get('invoice_code')

            invoice_extension = full_path_invoice.split('.')[-1]

            if invoice_extension == 'jpg' or invoice_extension == 'JPG' or invoice_extension == 'png' or invoice_extension == 'PNG':
                w, h, fname, filename = proc.scan_form(invoice_code, full_path_invoice)
                extract_text(filename, invoice_code, submission_id)
            else:
                text_pdf = full_path_invoice
                f, final_path = proc.pdf2img(invoice_code, full_path_invoice)
                extract_text(final_path, invoice_code, submission_id)
            
            print(full_path_invoice)
            if invoice_extension == 'jpg' or invoice_extension == 'JPG' or invoice_extension == 'png' or invoice_extension == 'PNG':
                pdf_name, text_pdf = proc.convert_to_pdf(invoice_code, filename)
            else:
                text_pdf = full_path_invoice
            
            tabs, proc_file = proc.get_table_details(invoice_code, text_pdf, submission_id)
            
            # dfs = []
            # for table in tables:
            #     dfs.append(table.df)
            
            # print(dfs)
            # dicts = []
            # for df in dfs:
            #     d = df.to_dict('records')
            #     dicts.append(d)

            data = pd.read_csv(proc_file)
            print(data) 
            d = data.to_dict('records')
            cols = list(data)
            print(list(data))
            print(d)

            #tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : data, 'dicts' : d, 'submission_id' : submission_id})
            tables.insert({'table_id' : table_id, 'invoice_code' : invoice_code, 'cols' : cols, 'data' : proc_file, 'submission_id' : submission_id})

    return json.dumps({'upload' : 'sucesss'})


# Extra functions

def detect_text_new(path, form_code, submission_id):
    submissions = mongo.db.submissions
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType
    paragraphs = []
    lines = []

    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                para = ""
                line = ""
                for word in paragraph.words:
                    for symbol in word.symbols:
                        line += symbol.text
                        if symbol.property.detected_break.type == breaks.SPACE:
                            line += ' '
                        if symbol.property.detected_break.type == breaks.EOL_SURE_SPACE:
                            line += ' '
                            lines.append(line)
                            para += line
                            line = ''
                        if symbol.property.detected_break.type == breaks.LINE_BREAK:
                            lines.append(line)
                            para += line
                            line = ''

                print(para)
                print(paragraph.bounding_box)
                paragraphs.append(para)

    print(paragraphs)

    print(lines)


def extract_text_batch(path, form_code, submission_id):

    submissions = mongo.db.submissions_batch
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

    section_bb = []
    section_titles = []
    keys = []
    values = []
    bb_coor = []


    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # print('\nBlock BB : {}\n'.format(block.bounding_box))
            # print('\nBlock confidence: {}\n'.format(block.confidence))
            words = []
            for paragraph in block.paragraphs:
                #print('Paragraph confidence: {}'.format(
                 #   paragraph.confidence))

                for word in paragraph.words:
                    '''word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])'''
                    t_list = []
                    for symbol in word.symbols:
                        if symbol.property.detected_break.type == breaks.LINE_BREAK or symbol.property.detected_break.type == breaks.EOL_SURE_SPACE:
                            t_list.append(symbol.text)
                            t_list.append('\n')
                        else:
                            t_list.append(symbol.text)
                    word_text = ''.join(t_list)
                    words.append(word_text)
                    # print('Word text: {} (confidence: {})'.format(
                    #    word_text, word.confidence))
                    # for symbol in word.symbols:
                        #print('\tSymbol: {} (confidence: {})'.format(
                        #     symbol.text, symbol.confidence))
            block_sentence = str(' '.join(words[0:len(words)]))
            print("\nBlock Sentence : {}".format(block_sentence))
            block_sentence_raw = "%r" % (block_sentence)
            print(block_sentence_raw)

            if ':' in block_sentence:
                block_titles = block_sentence.split(':')
                block_title = block_titles[0]
                block_content = ' '.join(block_titles[1:])
                block_category = get_category(block_sentence)
                bb = block.bounding_box
                serialized_bb = MessageToJson(bb)
                d = json.loads(serialized_bb)

                x1 = d['vertices'][0]['x']
                x2 = d['vertices'][1]['x']

                y1 = d['vertices'][0]['y']
                y2 = d['vertices'][2]['y']

                bb_coordinates = {'x1' : x1, 'x2' : x2, 'y1' : y1, 'y2' : y2}
                if block_category == 'NIL':
                    keys.append(block_title)
                    values.append(block_content)
                else:
                    keys.append(block_category)
                    values.append(block_sentence)
                bb_coor.append(bb_coordinates)

    image = cv2.imread(path)
    w = image.shape[0]
    h = image.shape[1]

    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    title = '%s - %s' % (form_code, timestamp)
    submissions.insert({'submission_id': submission_id, 'w' : w, 'h' : h, 'file' : path, 'invoice_code' : form_code, 'title' : title, 'coordinates' : bb_coor, 'keys' : keys, 'values' : values, 'timestamp' : timestamp, 'uploaded_by' : 'aniruddh'})

    return section_bb, section_titles


def extract_text(path, form_code, submission_id):

    submissions = mongo.db.submissions
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

    section_bb = []
    section_titles = []
    keys = []
    values = []
    bb_coor = []


    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # print('\nBlock BB : {}\n'.format(block.bounding_box))
            # print('\nBlock confidence: {}\n'.format(block.confidence))
            words = []
            for paragraph in block.paragraphs:
                #print('Paragraph confidence: {}'.format(
                 #   paragraph.confidence))

                for word in paragraph.words:
                    '''word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])'''
                    t_list = []
                    for symbol in word.symbols:
                        if symbol.property.detected_break.type == breaks.LINE_BREAK or symbol.property.detected_break.type == breaks.EOL_SURE_SPACE:
                            t_list.append(symbol.text)
                            t_list.append('\n')
                        else:
                            t_list.append(symbol.text)
                    word_text = ''.join(t_list)
                    words.append(word_text)
                    # print('Word text: {} (confidence: {})'.format(
                    #    word_text, word.confidence))
                    # for symbol in word.symbols:
                        #print('\tSymbol: {} (confidence: {})'.format(
                        #     symbol.text, symbol.confidence))
            block_sentence = str(' '.join(words[0:len(words)]))
            print("\nBlock Sentence : {}".format(block_sentence))
            block_sentence_raw = "%r" % (block_sentence)
            print(block_sentence_raw)

            if ':' in block_sentence:
                block_titles = block_sentence.split(':')
                block_title = block_titles[0]
                block_content = ' '.join(block_titles[1:])
                block_category = get_category(block_sentence)
                bb = block.bounding_box
                serialized_bb = MessageToJson(bb)
                d = json.loads(serialized_bb)

                x1 = d['vertices'][0]['x']
                x2 = d['vertices'][1]['x']

                y1 = d['vertices'][0]['y']
                y2 = d['vertices'][2]['y']

                bb_coordinates = {'x1' : x1, 'x2' : x2, 'y1' : y1, 'y2' : y2}
                if block_category == 'NIL':
                    keys.append(block_title)
                    values.append(block_content)
                else:
                    keys.append(block_category)
                    values.append(block_sentence)
                bb_coor.append(bb_coordinates)

    image = cv2.imread(path)
    w = image.shape[0]
    h = image.shape[1]

    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    title = '%s - %s' % (form_code, timestamp)
    submissions.insert({'submission_id': submission_id, 'w' : w, 'h' : h, 'file' : path, 'invoice_code' : form_code, 'title' : title, 'coordinates' : bb_coor, 'keys' : keys, 'values' : values, 'timestamp' : timestamp, 'uploaded_by' : 'aniruddh'})

    return section_bb, section_titles


def get_category(block_title):
    taxation_terms = ['GST', 'PAN', 'VAT', 'Service tax', 'CST']
    invoice_terms = ['Invoice', 'invoice']
    order_terms = ['orders', 'Orders', 'order', 'Order']
    
    if any(s in block_title for s in taxation_terms):
        category = 'Taxation Details'
    elif any(s in block_title for s in invoice_terms):
        category = 'Invoice Details'
    elif any(s in block_title for s in order_terms):
        category = 'Order Details'
    else:
        category = 'NIL'
    return category

def detect_text(path, form_code, submission_id):

    submissions = mongo.db.submissions
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

    section_bb = []
    section_titles = []
    keys = []
    values = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # print('\nBlock BB : {}\n'.format(block.bounding_box))
            # print('\nBlock confidence: {}\n'.format(block.confidence))
            words = []
            for paragraph in block.paragraphs:
                #print('Paragraph confidence: {}'.format(
                 #   paragraph.confidence))

                for word in paragraph.words:
                    '''word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])'''
                    t_list = []
                    for symbol in word.symbols:
                        if symbol.property.detected_break.type == breaks.LINE_BREAK or symbol.property.detected_break.type == breaks.EOL_SURE_SPACE:
                            t_list.append(symbol.text)
                            t_list.append('\n')
                        else:
                            t_list.append(symbol.text)
                    word_text = ''.join(t_list)
                    words.append(word_text)
                    # print('Word text: {} (confidence: {})'.format(
                    #    word_text, word.confidence))
                    # for symbol in word.symbols:
                        #print('\tSymbol: {} (confidence: {})'.format(
                        #     symbol.text, symbol.confidence))
            block_sentence = str(' '.join(words[0:len(words)]))
            print("\nBlock Sentence : {}".format(block_sentence))
            block_sentence_raw = "%r" % (block_sentence)
            print(block_sentence_raw)

            for i in range(len(block_sentence_raw)):
                if block_sentence_raw[i] == "\\" and block_sentence_raw [i+1] == "n":
                    sentences = block_sentence_raw.split('\\n')
                    print("asdoas", sentences)
                    block_content = ''
                    for sentence in sentences:
                        if ':' in sentence:
                            print("In")
                            print(sentence)
                            block_titles = sentence.split(':')
                            block_title = block_titles[0]
                            block_content = ' '.join(block_titles[1:])
                            keys.append(block_title)
                        else:
                            block_content += sentence
                    values.append(block_content)
                            
            else:
                if ':' in block_sentence:
                    block_titles = block_sentence.split(':')
                    block_title = block_titles[0]
                    block_content = ' '.join(block_titles[1:])
                    keys.append(block_title)
                    values.append(block_content)

    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    title = '%s - %s' % (form_code, timestamp)
    submissions.insert({'submission_id': submission_id, 'title' : title,  'invoice_code' : form_code, 'keys' : keys, 'values' : values, 'timestamp' : timestamp, 'uploaded_by' : session['username']})

    return section_bb, section_titles


def detect_document(path):
    del_list = ['-']
    """Detects document features in an image."""
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.document_text_detection(image=image)

    breaks = vision.enums.TextAnnotation.DetectedBreak.BreakType

    section_bb = []
    section_titles = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock BB : {}\n'.format(block.bounding_box))
            print('\nBlock confidence: {}\n'.format(block.confidence))
            words = []
            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(
                    paragraph.confidence))

                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    words.append(word_text)
                    # print('Word text: {} (confidence: {})'.format(
                    #    word_text, word.confidence))
                    # for symbol in word.symbols:
                        #print('\tSymbol: {} (confidence: {})'.format(
                        #     symbol.text, symbol.confidence))
            block_sentence = str(' '.join(words))
            print("\nBlock Sentence : {}".format(block_sentence))
            

            if ':' in block_sentence:
                block_titles = block_sentence.split(':')
                block_title = block_titles[0]
                print("\nBlock Title : {}\n".format(block_title))
                section_bb.append(block.bounding_box)
                section_titles.append(block_title)
    return section_bb, section_titles


def get_suggested_sections(form_code, invoice_file):
    invoices = mongo.db.invoices
    suggested_sections = mongo.db.suggested_sections
    bounding_boxes, titles = detect_document(invoice_file)
    for x in range(0, len(bounding_boxes)):
        bb = bounding_boxes[x]
        serialized_bb = MessageToJson(bb)
        d = json.loads(serialized_bb)

        x1 = d['vertices'][0]['x']
        x2 = d['vertices'][1]['x']

        y1 = d['vertices'][0]['y']
        y2 = d['vertices'][2]['y']


        title = titles[x]
        suggested_sections.insert({'invoice_code' : form_code, 'x1' : str(x1), 'x2' : str(x2), 'y1' : str(y1), 'y2' : str(y2), 'title' : title})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
