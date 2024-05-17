import os
import threading
import time
import pygame
import schedule
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from sqlalchemy.sql.expression import text
from flask_wtf import FlaskForm
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, db, Schedule
from formularios.forms import LoginForm, RegisterForm, CadastrarIntervalosForm



app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
migrate = Migrate(app, db)

pygame.mixer.init()
ALLOWED_EXTENSIONS = {'mp3'}

#db.init_app(app)
db = SQLAlchemy(app)

# Inicializa o sistema de login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha incorretos', 'error')
    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/cadastrar_intervalos', methods=['GET', 'POST'])
def cadastrar_intervalos():
    form = CadastrarIntervalosForm()
    if form.validate_on_submit():
        day = form.day.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        audio_file = request.files['audio_file']

        # Verifica se foi enviado um arquivo de áudio e se é um arquivo permitido
        if audio_file and allowed_file(audio_file.filename):
            # Salva o arquivo de áudio na pasta "audio" na raiz do seu programa
            filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
            audio_file.save(audio_path)

            # Salva o nome do arquivo e o caminho completo no banco de dados
            agenda = Schedule(
                day=day,
                start_time=start_time,
                end_time=end_time,
                audio_filename=filename,
                audio_path=audio_path,
                duration=30  # Você pode ajustar a duração conforme necessário
            )
            db.session.add(agenda)
            db.session.commit()

            flash('Intervalo cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastrar_intervalos'))

    agendas = Schedule.query.all()
    return render_template('cadastrarintervalos.html', form=form, agendas=agendas, translate_day=translate_day)

def translate_day(day):
    days_translation = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira'
    }
    return days_translation.get(day, day)  #tradução

@app.route('/editar_intervalo/<int:agenda_id>', methods=['POST'])
def editar_intervalo(agenda_id):
    if request.method == 'POST':
        agenda = Schedule.query.get(agenda_id)
        form = CadastrarIntervalosForm(obj=agenda)
        if request.method == 'POST' and form.validate():
            form.populate_obj(agenda)
            db.session.commit()
            flash('Intervalo editado com sucesso!', 'success')
            return redirect(url_for('cadastrar_intervalos'))
        return render_template('editar_intervalo.html', form=form, agenda=agenda)

@app.route('/excluir_intervalo/<int:agenda_id>', methods=['POST', 'DELETE'])
def excluir_intervalo(agenda_id):
    if request.method in ['POST', 'DELETE']:
        agenda = Schedule.query.get(agenda_id)
        if agenda:
            #db.session.delete(agenda)
            delete_query = text(str(Schedule.query.filter_by(id=agenda_id).delete()))
            print(delete_query)
            db.session.commit()
            flash('Intervalo excluído com sucesso!', 'success')
        else:
            flash('Intervalo não encontrado.', 'error')
    return redirect(url_for('cadastrar_intervalos'))

def check_schedule():
    # Verifica a hora atual
    now = datetime.now().time()
    current_time = now.strftime("%H:%M:%S")
    print("Verificando agenda...")
    print("Hora atual:", current_time)

    # Consulta o banco de dados para verificar se há agendamentos
    schedules = Schedule.query.all()
    print("Agendamentos encontrados:", schedules)

    for schedule in schedules:
        if schedule.start_time.strftime("%H:%M:%S") == current_time:
            # Reproduz o áudio associado ao agendamento
            print("Hora do agendamento encontrada:", schedule.start_time.strftime("%H:%M:%S"))
            play_audio(schedule.audio_path)

    print("Verificação da agenda concluída.")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3001, debug=True)
