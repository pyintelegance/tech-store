# -*- coding: utf-8 -*-
"""Формы (WTForms) с валидацией для магазина и админ-панели."""
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, FloatField, DecimalField, SubmitField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Regexp, Email

csrf = CSRFProtect()


class CheckoutForm(FlaskForm):
    """Оформление заказа: адрес обязателен, address2 — optional."""
    name = StringField("name", validators=[
        DataRequired(message="name_required"),
        Length(min=2, max=200, message="name_length"),
    ])
    phone = StringField("phone", validators=[
        DataRequired(message="phone_required"),
        Regexp(r"^\+?\d[\d\s\-()]{6,25}$", message="phone_invalid"),
    ])
    email = StringField("email", validators=[Optional(), Email(message="email_invalid"), Length(max=200)])
    city = SelectField("city", validators=[DataRequired(message="city_required")])
    address = StringField("address", validators=[
        DataRequired(message="address_required"),
        Length(min=5, max=500, message="address_length"),
    ])
    address2 = StringField("address2", validators=[Optional(), Length(max=500)])
    coupon = StringField("coupon", validators=[Optional(), Length(max=50)])
    submit = SubmitField("place_order")


class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired()])
    password = PasswordField("password", validators=[DataRequired()])
    submit = SubmitField("login")


class ProductForm(FlaskForm):
    category_id = SelectField("category", validators=[DataRequired()])
    name_ru = StringField("name_ru", validators=[DataRequired(), Length(max=200)])
    name_uz = StringField("name_uz", validators=[DataRequired(), Length(max=200)])
    description_ru = TextAreaField("description_ru", validators=[DataRequired()])
    description_uz = TextAreaField("description_uz", validators=[DataRequired()])
    price = DecimalField("price", validators=[DataRequired(), NumberRange(min=0)])
    old_price = DecimalField("old_price", validators=[Optional(), NumberRange(min=0)])
    stock = IntegerField("stock", validators=[DataRequired(), NumberRange(min=0)])
    image = StringField("image", validators=[Optional(), Length(max=255)])
    image_file = FileField("image_file", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Только изображения")])
    gallery_files = FileField("gallery_files", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Только изображения")])
    specs = TextAreaField("specs", validators=[Optional()])
    rating = DecimalField("rating", validators=[Optional(), NumberRange(min=0, max=5)])
    reviews = IntegerField("reviews", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("save")


class CategoryForm(FlaskForm):
    slug = StringField("slug", validators=[DataRequired(), Length(max=50)])
    name_ru = StringField("name_ru", validators=[DataRequired(), Length(max=100)])
    name_uz = StringField("name_uz", validators=[DataRequired(), Length(max=100)])
    icon = StringField("icon", validators=[DataRequired(), Length(max=10)])
    submit = SubmitField("save")


class CityForm(FlaskForm):
    name_ru = StringField("name_ru", validators=[DataRequired(), Length(max=100)])
    name_uz = StringField("name_uz", validators=[DataRequired(), Length(max=100)])
    delivery_price = DecimalField("delivery_price", validators=[DataRequired(), NumberRange(min=0)])
    delivery_minutes = IntegerField("delivery_minutes", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("save")


class CouponForm(FlaskForm):
    code = StringField("code", validators=[DataRequired(), Length(max=50)])
    discount_percent = IntegerField("discount_percent", validators=[DataRequired(), NumberRange(min=1, max=100)])
    submit = SubmitField("save")


class AdminForm(FlaskForm):
    username = StringField("username", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("password", validators=[DataRequired(), Length(min=4, max=200)])
    role = SelectField("role", choices=[("manager", "Менеджер"), ("superadmin", "Генеральный")])
    permissions = StringField("permissions", validators=[Optional()])
    submit = SubmitField("save")


class AdminEditForm(FlaskForm):
    username = StringField("username", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("password", validators=[Optional(), Length(min=4, max=200)])
    role = SelectField("role", choices=[("manager", "Менеджер"), ("superadmin", "Генеральный")])
    permissions = StringField("permissions", validators=[Optional()])
    submit = SubmitField("save")