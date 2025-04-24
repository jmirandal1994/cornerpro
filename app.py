from flask import Flask, request, render_template, redirect, session
from dotenv import load_dotenv
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Cargar variables de entorno
load_dotenv()

from supabase_client import supabase

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# Variables para envío de correos
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

def enviar_correo(asunto, cuerpo):
    try:
        msg = EmailMessage()
        msg['Subject'] = asunto
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_DESTINO
        msg.set_content(cuerpo)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

def formatear_fecha(fecha_iso):
    try:
        fecha = datetime.fromisoformat(fecha_iso.replace('Z', '+00:00'))
        return fecha.strftime('%d/%m/%Y')
    except Exception as e:
        print(f"Error al formatear fecha: {e}")
        return "Fecha desconocida"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        response = supabase.table('usuarios')\
            .select("*")\
            .eq("username", username)\
            .eq("password", password)\
            .execute()

        users = response.data

        if not users:
            return "Credenciales inválidas"

        user = users[0]
        session['username'] = user['username']
        session['role'] = user['role']
        return redirect('/dashboard')

    tipo = request.args.get('tipo', 'inversor')
    return render_template('login.html', user_type=tipo)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    user_data = supabase.table('usuarios')\
        .select('*')\
        .eq('username', session['username'])\
        .execute().data[0]

    monto_inicial = float(user_data.get('monto_inicial', 0))
    monto_actual = float(user_data.get('monto_actual', 0))
    partidos_invertidos = int(user_data.get('partidos_invertidos', 0))

    try:
        porcentaje_crecimiento = round(((monto_actual - monto_inicial) / monto_inicial) * 100, 2)
    except ZeroDivisionError:
        porcentaje_crecimiento = 0

    fecha_creacion = formatear_fecha(user_data.get('created_at', ''))

    if request.method == 'POST':
        tipo_formulario = request.form.get("tipo")
        mensaje = request.form.get("mensaje", "")
        asunto = ""
        cuerpo = f"Usuario: {session['username']}\n\n"

        if tipo_formulario == "consulta":
            asunto = "Nueva consulta de usuario"
            cuerpo += f"Consulta:\n{mensaje}"
        elif tipo_formulario == "incrementar":
            asunto = "Solicitud de incremento de capital"
            cuerpo += "El usuario ha solicitado incrementar su capital."
        elif tipo_formulario == "retiro":
            asunto = "Solicitud de retiro"
            cuerpo += "El usuario ha solicitado un retiro de fondos."

        enviar_correo(asunto, cuerpo)
        session['mensaje_enviado'] = "✅ ¡Tu solicitud fue enviada correctamente!"
        return redirect('/dashboard')

    mensaje_enviado = session.pop('mensaje_enviado', None)

    return render_template('dashboard.html',
        username=session['username'],
        monto_inicial=monto_inicial,
        monto_actual=monto_actual,
        partidos_invertidos=partidos_invertidos,
        porcentaje_crecimiento=porcentaje_crecimiento,
        fecha_creacion=fecha_creacion,
        mensaje_enviado=mensaje_enviado
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        existing = supabase.table('usuarios')\
            .select("*")\
            .eq("username", username)\
            .execute()

        if existing.data:
            return "Este usuario ya existe."

        supabase.table('usuarios')\
            .insert({
                'username': username,
                'password': password,
                'role': role,
                'created_at': datetime.utcnow().isoformat()
            })\
            .execute()

        return redirect('/login')

    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')

