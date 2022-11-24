import pyrebase
import json
from requests.exceptions import HTTPError
from config import Config
from flask import Flask, session, request, redirect, render_template, flash, url_for, send_file
import os
from core.helper import BigQueryClient
import pandas as pd

# -----------------------------------------------------------------------------------------------------

PROJECT_ID = 'gobiz-solution'

# -----------------------------------------------------------------------------------------------------

with open('./core/firebaseConfig.json', 'r') as f:
    config = json.load(f)

# -----------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# -----------------------------------------------------------------------------------------------------

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

# -----------------------------------------------------------------------------------------------------

client = BigQueryClient('./core/BigquerryCredential.json', PROJECT_ID)
schemas = client.get_schemas()

first_schema = list(schemas.keys())[0]
first_table = list(schemas.get(first_schema))[0]

state = {
    'project': PROJECT_ID,
    'schema': first_schema, 
    'table': first_table,
    'view': 'Table'
}

# -----------------------------------------------------------------------------------------------------
@app.get('/')
def index_get():
    global state
    global schemas
    
    if ('user' in session):
        return redirect(url_for('homepage_get'))
    return render_template('login.html')


@app.post('/')
def index_post():
    global state
    global schemas
    
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        if request.form.get('remember_me'):
            session['user'] = user
        return redirect(url_for('homepage_get', schemas=schemas, state=state))
    except HTTPError as err:
        flash('Wrong username of password. Please try again')
        return redirect(url_for('index_get'))


@app.get('/forget_password')
def forget_password_get():
    return render_template('forgot_password.html')


@app.post('/forget_password')
def forget_password_post():
    email = request.form.get('email')
    try:
        auth.send_password_reset_email(email)
    except:
        flash('Invalid Email')
    else:
        flash('An email for reset your password has been sent to your email. Please make sure to also check your spambox.')
    return redirect(url_for('index_get'))


@app.get('/homepage')
def homepage_get():
    global state
    return render_template('homepage.html', schemas=schemas, state=state)


@app.post('/homepage')
def homepage_post():
    global state
    global schemas
    
    if 'choose_table' in request.form:
        state['schema'], state['table'] = request.form.get('choose_table').split('.')
        
    if 'change_view' in request.form:
        state['view'] = request.form.get('change_view')
        
    if 'cancel' in request.form:
        return render_template('homepage.html', schemas=schemas, state=state)
    
    if 'download_csv' in request.form:
        file_name = client.download_csv(state.get('project'), state.get('schema'), state.get('table'))
        return send_file(file_name, as_attachment=True)
    
    if 'download_json' in request.form:
        path = client.download_json(state.get('project'), state.get('schema'), state.get('table'))
        return send_file(path, as_attachment=True)
    
    if ('delete_table' in request.form):
        schema, table = request.form.get('delete_table').split('.')
        client.delete_table(schema, table)
        flash(f"Successfully drop the table { table }")
        schemas = client.get_schemas()
        first_schema = list(schemas.keys())[0]
        first_table = list(schemas.get(first_schema))[0]
        state = {
            'project': PROJECT_ID,
            'schema': first_schema, 
            'table': first_table,
            'view': 'Table'
        }
        
    if ('add_new_column' in request.form):
        project = state.get('project')
        schema = state.get('schema')
        table = state.get('table')
        
        column = request.form.get('new_column')
        type = request.form.get('new_type')
        try:
            if (client.add_column(project, schema, table, column, type)):
                flash(
                    f'Successfully add column {column} into table {table}')
            else:
                flash(f'Cannot add column {column} into table {table}')
        except Exception as e:
            return render_template('error.html')
        
    if ('append' in request.form):
        project = state.get('project')
        schema = state.get('schema')
        table = state.get('table')
        
        columns = schemas.get(schema).get(table)
        user_inputs = list()
        for column in columns:
            user_inputs.append(request.form.get(column))
            row_to_insert = [dict(zip(columns, user_inputs))]

            try:
                if (client.append(project, schema, table, row_to_insert)):
                    flash(
                        f'Successfully append column into table {table}')
                else:
                    flash(f'Cannot append column into table {table}')
            except Exception as e:
                return render_template('error.html')
    
    if ('uploaded_file' in request.form):
        upload_schema = request.form.get('uploaded_file')
        uploaded_file = request.files['new_file']
        table_name = request.form.get('new_table_name')
        df = pd.read_csv(uploaded_file)
        client.load_table_from_df(df, upload_schema, table_name)
        
    if ('define_new_shema' in request.form):
        project = state.get('project')
        schema = state.get('schema')
        table = request.form.get('new_define_table')
        columns = json.loads(request.form.get('final_schema'))
        df = pd.DataFrame({''.join(e for e in c if e.isalnum()): pd.Series(dtype=t)
                              for c, t in columns.items()})
        client.load_table_from_dataframe(
                df, f'{project}.{schema}.{table}')
        
    return render_template('homepage.html', schemas=schemas, state=state)

# -----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
