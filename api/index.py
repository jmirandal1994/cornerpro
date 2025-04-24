
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, static_folder="../static", template_folder="../templates")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if user_type == 'admin' and username == 'admin' and password == 'cornerpro2025':
            return redirect(url_for('admin'))
        elif user_type == 'inversor' and username == 'Rodrigoliva' and password == '123456':
            return redirect(url_for('investor'))
        else:
            return "Usuario o contraseña incorrectos"

    return render_template('login.html', user_type=user_type)

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/investor')
def investor():
    return render_template('investor.html')

def handler(environ, start_response):
    return app(environ, start_response)
