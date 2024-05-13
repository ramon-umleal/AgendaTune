from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TimeField, FileField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Usuário já existe. Por favor, escolha outro.')

class CadastrarIntervalosForm(FlaskForm):
    day = SelectField('Dia da Semana', choices=[('Monday', 'Segunda-feira'), ('Tuesday', 'Terça-feira'), ('Wednesday', 'Quarta-feira'), ('Thursday', 'Quinta-feira'), ('Friday', 'Sexta-feira')])
    start_time = TimeField('Horário de Início', validators=[DataRequired()])
    end_time = TimeField('Horário de Término', validators=[DataRequired()])
    audio_file = FileField('Áudio')
    submit = SubmitField('Salvar')