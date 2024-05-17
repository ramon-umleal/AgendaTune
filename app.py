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

db.init_app(app)
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
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    return days_translation.get(day, day)  # tradução

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
            db.session.delete(agenda)
            db.session.commit()
            flash('Intervalo excluído com sucesso!', 'success')
        else:
            flash('Intervalo não encontrado.', 'error')
    return redirect(url_for('cadastrar_intervalos'))


def play_audio(audio_path):
    try:
        print("Tentando reproduzir áudio:", audio_path)
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        print("Áudio reproduzido com sucesso!")
    except Exception as e:
        print("Erro ao reproduzir áudio:", str(e))


def check_schedule():
    with app.app_context():
        while True:
            # hora atual
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_day = now.strftime("%A")  # Obtém o dia da semana atual
            print("Verificando agenda...")
            print("Hora atual:", current_time)
            print("Dia da semana atual:", current_day)

            # Consulta o banco de dados para verificar se há agendamentos
            schedules = Schedule.query.all()
            print("Número de agendamentos encontrados:", len(schedules))  # Mensagem de depuração
            for schedule in schedules:
                schedule_day = translate_day(schedule.day)  # Traduz o dia agendado
                print("Dia do agendamento:", schedule_day)  # Mensagem de depuração
                print("Hora do agendamento:", schedule.start_time.strftime("%H:%M:%S"))  # Mensagem de depuração
                if schedule_day == current_day and schedule.start_time.strftime("%H:%M:%S") == current_time:
                    # Reproduz o áudio associado ao agendamento
                    print("Hora do agendamento encontrada:", schedule.start_time.strftime("%H:%M:%S"))
                    print("Reproduzindo áudio:", schedule.audio_path)
                    play_audio(schedule.audio_path)

            time.sleep(30)  # Aguarda 30 segundos antes de verificar novamente

# Inicia a thread para verificar o agendamento
schedule_thread = threading.Thread(target=check_schedule)
schedule_thread.start()



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3001, debug=True)
