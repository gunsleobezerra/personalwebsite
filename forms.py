from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     RadioField, SelectField, SubmitField, PasswordField)
from wtforms.validators import DataRequired, Email, Length, EqualTo
import mywebsite as mw
class LoginForm(FlaskForm):
    username= StringField('username', [DataRequired()])
    password= PasswordField('Password', [DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
    
    #inicia classe LoginForm herda de Form
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
    
    #validar dados do formulario
    def validate(self):
        if not FlaskForm.validate(self):
            return False
        user = mw.User.query.filter_by(username=self.username.data).first()
        print(user)
        if user is None:
            self.username.errors.append('Invalid email or password')
            return False
        if not user.check_password(self.password.data):
            self.username.errors.append('Invalid email or password')
            return False
        return True
    
