from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
import re

# 导入班级排序工具
from class_sorting_utils import generate_class_sorting_sql

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=2, max=20, message='用户名长度必须在2-20个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, max=128, message='密码长度必须在6-128个字符之间')
    ])
    remember_me = BooleanField('记住我')

class InfoCommitteeRegistrationForm(FlaskForm):
    class_name = SelectField('班级', validators=[DataRequired(message='请选择你的班级')])
    
    real_name = StringField('姓名', validators=[
        DataRequired(message='请输入你的姓名'),
        Length(min=2, max=10, message='姓名长度必须在2-10个字符之间')
    ])

    initial_password = PasswordField('初始密码', validators=[
        DataRequired(message='请输入管理员下发的初始密码'),
        Length(min=6, max=128, message='密码长度不正确')
    ])
    
    new_password = PasswordField('设置新密码', validators=[
        DataRequired(message='请输入你的新密码'),
        Length(min=6, max=128, message='新密码长度必须在6-128个字符之间')
    ])
    
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次输入的新密码不一致')
    ])

    def __init__(self, *args, **kwargs):
        super(InfoCommitteeRegistrationForm, self).__init__(*args, **kwargs)
        # 动态填充班级选项
        from db import get_conn, put_conn
        conn = get_conn()
        try:
            cur = conn.cursor()
            # 只选择当前活跃学期中配置的班级
            class_sorting_sql = generate_class_sorting_sql("sc.grade_name", "sc.class_name")
            cur.execute(f"""
                SELECT sc.class_name
                FROM semester_classes sc
                JOIN semester_config s ON sc.semester_id = s.id
                WHERE s.is_active = 1 AND sc.is_active = 1
                ORDER BY {class_sorting_sql}
            """)
            # 生成选项
            self.class_name.choices = [('', '请选择班级')] + [(c['class_name'], c['class_name']) for c in cur.fetchall()]
        finally:
            put_conn(conn)

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

    note = TextAreaField('备注', validators=[Length(max=50, message='备注不能超过50个字符')])

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
