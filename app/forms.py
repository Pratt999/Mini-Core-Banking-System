from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from app.models import Customer, Account

class LoginForm(FlaskForm):
    username = StringField('Username (or Email)', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class CustomerForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=7, max=15)])
    address = TextAreaField('Physical Address', validators=[DataRequired()])
    submit = SubmitField('Save Customer')

class AccountForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    account_type = SelectField('Account Type', choices=[('savings', 'Savings'), ('checking', 'Checking'), ('business', 'Business')], validators=[DataRequired()])
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('INR', 'INR')], default='USD')
    initial_deposit = FloatField('Initial Deposit', validators=[NumberRange(min=0)], default=0.0)
    submit = SubmitField('Open Account')

class TransactionForm(FlaskForm):
    transaction_type = SelectField('Type', choices=[('deposit', 'Deposit'), ('withdrawal', 'Withdrawal'), ('transfer', 'Transfer')], validators=[DataRequired()])
    account_id = SelectField('From Account', coerce=int, validators=[DataRequired()])
    target_account_id = SelectField('To Account (Transfers Only)', coerce=int, choices=[(0, '-- None --')])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    description = StringField('Description / Reference', validators=[Length(max=200)])
    submit = SubmitField('Process Transaction')
    
    def validate_target_account_id(self, field):
        if self.transaction_type.data == 'transfer' and (not field.data or field.data == 0):
            raise ValidationError('Target account is required for transfers.')
        if field.data and field.data == self.account_id.data:
            raise ValidationError('Cannot transfer to the same account.')

class LoanApplicationForm(FlaskForm):
    customer_id = SelectField('Select Applicant', coerce=int, validators=[DataRequired()])
    amount = FloatField('Requested Amount', validators=[DataRequired(), NumberRange(min=1000)])
    tenure = SelectField('Tenure (Months)', choices=[(12, '12 Months'), (24, '24 Months'), (36, '36 Months'), (60, '60 Months')], coerce=int)
    submit = SubmitField('Submit Application')
