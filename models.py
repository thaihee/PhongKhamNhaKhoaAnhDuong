from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, Float, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as RoleEnum
from PhongKhamNhaKhoa import app, db
from datetime import datetime


class UserRole(RoleEnum):
    ADMIN = 1
    DOCTOR = 2
    STAFF = 3
    USER = 4


class Gender(RoleEnum):
    NAM = "Nam"
    NU = "Nữ"
    KHAC = "Khác"


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String(150), nullable=False)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    dob = Column(Date)
    gender = Column(Enum(Gender), default=Gender.NAM)
    patient_profile = relationship('Patient', backref='user', uselist=False)
    doctor_profile = relationship('Doctor', backref='user', uselist=False)
    staff_profile = relationship('Staff', backref='user', uselist=False)

class Doctor(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100))
    user_id = Column(Integer, ForeignKey('user.id'))
    appointments = relationship('Appointment', backref='doctor')


class Patient(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    phone = Column(String(15))
    user_id = Column(Integer, ForeignKey('user.id'))
    appointments = relationship('Appointment', backref='patient')
    profile = relationship('PatientProfile', backref='patient', uselist=False)


class Staff(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_date = Column(Date, default=datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))

    bills = relationship('Bill', backref='staff')

class Appointment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    time_slot = Column(String(20))
    service_type = Column(String(100))
    status = Column(String(50), default="Đã đặt")

    patient_id = Column(Integer, ForeignKey('patient.id'))
    doctor_id = Column(Integer, ForeignKey('doctor.id'))
    treatment_sheet = relationship('TreatmentSheet', back_populates='appointment', uselist=False)
    bill = relationship('Bill', back_populates='appointment', uselist=False)


class Medicine(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    unit = Column(String(20))
    price = Column(Float, default=0)
    expiry_date = Column(Date, nullable=False)


class Service(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)


class TreatmentService(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    treatment_id = Column(Integer, ForeignKey('treatment_sheet.id'))
    service_id = Column(Integer, ForeignKey('service.id'))
    note = Column(Text)
    service = relationship('Service', backref='treatment_details')


class TreatmentSheet(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis = Column(String(255))
    created_date = Column(DateTime, default=datetime.now)
    note = Column(Text)
    appointment_id = Column(Integer, ForeignKey('appointment.id'))
    appointment = relationship('Appointment', back_populates='treatment_sheet')
    services = relationship('TreatmentService', backref='treatment_sheet')
    details = relationship('PrescriptionDetail', backref='treatment_sheet')


class PrescriptionDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    treatment_id = Column(Integer, ForeignKey('treatment_sheet.id'))
    medicine_id = Column(Integer, ForeignKey('medicine.id'))
    instruction = Column(String(255))
    dosage = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    days = Column(Integer, nullable=False)
    medicine = relationship('Medicine', backref='prescription_details')


class Bill(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_fee = Column(Float, default=0)
    medicine_fee = Column(Float, default=0)
    vat = Column(Float, default=0.1)
    created_date = Column(DateTime, default=datetime.now)
    total_amount = Column(Float, nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointment.id'), nullable=False)
    appointment = relationship('Appointment', back_populates='bill')

    discount_amount = Column(Float, default=0)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    coupon_id = Column(Integer, ForeignKey('coupon.id'), nullable=True)
    profile_id = Column(Integer, ForeignKey('patient_profile.id'), nullable=False)


class Coupon(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    type = Column(String(10), default='percent')
    value = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime)

    bills = relationship('Bill', backref='coupon')


class PatientProfile(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    medical_history = Column(Text)
    total_spent = Column(Float, default=0)
    created_date = Column(DateTime, default=datetime.now)

    patient_id = Column(Integer, ForeignKey('patient.id'), unique=True)
    bills = relationship('Bill', backref='profile')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()