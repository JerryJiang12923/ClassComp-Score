from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
import re

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=20, message='用户名长度必须在3-20个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
    ])
    remember_me = BooleanField('记住我')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=20, message='用户名长度必须在3-20个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=120, message='邮箱长度不能超过120个字符')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    class_name = SelectField('班级', choices=[
        ('', '请选择班级'),
        ('中预1班', '中预1班'),
        ('中预2班', '中预2班'),
        ('中预3班', '中预3班'),
        ('中预4班', '中预4班'),
        ('中预5班', '中预5班'),
        ('中预6班', '中预6班'),
        ('中预7班', '中预7班'),
        ('中预8班', '中预8班'),
        ('初一1班', '初一1班'),
        ('初一2班', '初一2班'),
        ('初一3班', '初一3班'),
        ('初一4班', '初一4班'),
        ('初一5班', '初一5班'),
        ('初一6班', '初一6班'),
        ('初一7班', '初一7班'),
        ('初一8班', '初一8班'),
        ('初二1班', '初二1班'),
        ('初二2班', '初二2班'),
        ('初二3班', '初二3班'),
        ('初二4班', '初二4班'),
        ('初二5班', '初二5班'),
        ('初二6班', '初二6班'),
        ('初二7班', '初二7班'),
        ('初二8班', '初二8班'),
        ('高一1班', '高一1班'),
        ('高一2班', '高一2班'),
        ('高一3班', '高一3班'),
        ('高一4班', '高一4班'),
        ('高一5班', '高一5班'),
        ('高一6班', '高一6班'),
        ('高二1班', '高二1班'),
        ('高二2班', '高二2班'),
        ('高二3班', '高二3班'),
        ('高二4班', '高二4班'),
        ('高二5班', '高二5班'),
        ('高二6班', '高二6班'),
        ('高二7班', '高二7班'),
        ('高二8班', '高二8班'),
        ('高一VCE', '高一VCE'),
        ('高二VCE', '高二VCE'),
        ('管理员', '管理员')
    ], validators=[DataRequired(message='请选择班级')])

    def validate_username(self, username):
        if not re.match(r'^[a-zA-Z0-9_]+$', username.data):
            raise ValidationError('用户名只能包含字母、数字和下划线')

class ScoreForm(FlaskForm):
    target_grade = SelectField('被查年级', choices=[
        ('', '请选择年级'),
        ('中预', '中预'),
        ('初一', '初一'),
        ('初二', '初二'),
        ('高一', '高一'),
        ('高二', '高二'),
        ('VCE', 'VCE')
    ], validators=[DataRequired(message='请选择被查年级')])
    
    score1 = IntegerField('电脑整洁', validators=[
        DataRequired(message='请输入分数'),
        NumberRange(min=0, max=3, message='分数必须在0-3之间')
    ])
    
    score2 = IntegerField('物品摆放', validators=[
        DataRequired(message='请输入分数'),
        NumberRange(min=0, max=3, message='分数必须在0-3之间')
    ])
    
    score3 = IntegerField('使用情况', validators=[
        DataRequired(message='请输入分数'),
        NumberRange(min=0, max=4, message='分数必须在0-4之间')
    ])
    
    note = TextAreaField('备注', validators=[Length(max=200, message='备注不能超过200个字符')])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[
        DataRequired(message='请输入当前密码'),
        Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请确认新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])