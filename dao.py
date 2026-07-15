import hashlib

from sqlalchemy import func

from PhongKhamNhaKhoa import db
from PhongKhamNhaKhoa.models import User, TreatmentService, Coupon, PrescriptionDetail, TreatmentSheet, PatientProfile
from PhongKhamNhaKhoa.models import Appointment, Medicine, Bill, Patient, Doctor, Service
from datetime import date, datetime


def auth_user(username, password):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()
    return User.query.filter(User.username == username, User.password == password).first()


def add_user(fullname,username,password, dob, gender):
    password = hashlib.md5(password.encode('utf-8')).hexdigest()
    u = User(fullname=fullname,username=username.strip(),password=password.strip(), dob=dob, gender=gender)
    db.session.add(u)
    db.session.commit()

# Xử lý thêm lịch khám
def add_appointment(user_id, name, time_slot, phone, date_str, doctor_id, service_type):

    p = Patient.query.filter(Patient.user_id == user_id).first()
    if not p:
        p = Patient(name=name, phone=phone, user_id=user_id)
        db.session.add(p)
        db.session.commit()

    count = Appointment.query.filter(Appointment.date == date_str,
                                     Appointment.doctor_id == doctor_id).count()
    if count >= 5:
        return False, "Bác sĩ đã nhận đủ 5 lịch khám trong ngày này!"

    checkTrungGio = Appointment.query.filter(
        Appointment.date == date_str,
        Appointment.doctor_id == doctor_id,
        Appointment.time_slot == time_slot
    ).first()

    if checkTrungGio:
        return False, f"Bác sĩ đã có lịch hẹn vào lúc {time_slot}. Vui lòng chọn khung giờ khác!"


    new_app = Appointment(
        date=date_str,
        time_slot=time_slot,
        service_type=service_type,
        patient_id=p.id,
        doctor_id=doctor_id,
        status="Đã đặt"
    )
    db.session.add(new_app)
    db.session.commit()
    return True, "Đăng ký thành công!"

def get_all_doctors():
    return Doctor.query.all()

def get_services():
    return Service.query.all()

def get_doctor_by_user_id(user_id):
    return Doctor.query.filter_by(user_id=user_id).first()

def get_appointments_by_doctor(doctor_id, d=None):
    if d is None:
        from datetime import date
        d = date.today()
    return Appointment.query.filter_by(doctor_id=doctor_id, date=d).all()

def add_treatment_record(appointment_id, diagnosis, service_ids, note):
    try:
        ts = TreatmentSheet(
            appointment_id=appointment_id,
            diagnosis=diagnosis,
            note=note
        )
        db.session.add(ts)
        db.session.flush()

        if service_ids:
            for s_id in service_ids:
                if s_id:
                    dt = TreatmentService(
                        treatment_id=ts.id,
                        service_id=int(s_id)
                    )
                    db.session.add(dt)

        db.session.commit()
        return ts
    except Exception as e:
        print(f"Lỗi DAO: {e}")
        db.session.rollback()
        return None

def update_appointment_status(appointment_id, new_status):
    apt = Appointment.query.get(appointment_id)
    if apt:
        apt.status = new_status
        db.session.commit()

def get_medicines():
    return Medicine.query.filter(Medicine.expiry_date >= date.today()).all()

def is_medicine_valid(medicine_id):
    m = Medicine.query.get(medicine_id)
    if m and m.expiry_date < date.today():
        return False
    return True


def add_prescription_detail(treatment_id, medicine_id, dosage, unit, days, note):
    try:
        d = PrescriptionDetail(
            treatment_id=treatment_id,
            medicine_id=medicine_id,
            dosage=float(dosage),
            unit=unit,
            days=int(days),
            instruction=note
        )
        db.session.add(d)
        db.session.commit()
        return True
    except Exception as ex:
        print(ex)
        db.session.rollback()
        return False

def get_treament_sheet_by_id(treatment_id):
    return TreatmentSheet.query.get(treatment_id)


def get_bill_details(treatment_id, coupon_code=None):
    from PhongKhamNhaKhoa.models import TreatmentSheet, Coupon
    ts = TreatmentSheet.query.get(treatment_id)
    service_total = sum(s.service.price for s in ts.services if s.service)
    medicine_total = sum((d.dosage * d.days) * d.medicine.price for d in ts.details if d.medicine)
    subtotal = service_total + medicine_total
    discount_amount = 0
    coupon_obj = None
    if coupon_code:
        coupon_obj = Coupon.query.filter(
            Coupon.code == coupon_code.strip().upper(),
            Coupon.active == True
        ).first()
        if coupon_obj:
            if coupon_obj.type == 'percent':
                discount_amount = subtotal * (coupon_obj.value / 100)
            else:
                discount_amount = coupon_obj.value
    total_after_discount = subtotal - discount_amount
    vat = total_after_discount * 0.1
    total_final = total_after_discount + vat
    return {
        'ts': ts,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'vat': vat,
        'total_amount': total_final,
        'coupon_obj': coupon_obj,
        'service_total': service_total,
        'medicine_total': medicine_total
    }

def confirm_payment(appointment_id, service_fee, medicine_fee, discount, total_amount, staff_id, profile_id, coupon_id=None):
    try:
        new_bill = Bill(
            service_fee=service_fee,
            medicine_fee=medicine_fee,
            discount_amount=discount,
            coupon_id=coupon_id,
            total_amount=total_amount,
            appointment_id=appointment_id,
            staff_id = staff_id,
            profile_id = profile_id
        )
        db.session.add(new_bill)

        profile = PatientProfile.query.get(profile_id)
        if profile:
            if profile.total_spent is None:
                profile.total_spent = 0
            profile.total_spent += total_amount

        apt = Appointment.query.get(appointment_id)
        if apt:
            apt.status = "Đã thanh toán"
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def get_appointments_by_status(status):
    from PhongKhamNhaKhoa.models import Appointment
    return Appointment.query.filter_by(status=status).all()

def get_all_appointments():
    return Appointment.query.all()

def lay_danh_sach_bac_si():
    return db.session.query(Doctor.id, User.fullname).join(User, Doctor.user_id == User.id).all()


def thong_ke_doanh_thu(thang, nam, ma_bac_si=None):
    query = db.session.query(
        func.date(Bill.created_date).label('ngay'),
        func.sum(Bill.total_amount).label('tong')
    ).join(Appointment, Bill.appointment_id == Appointment.id)

    query = query.filter(func.extract('month', Bill.created_date) == thang,
                         func.extract('year', Bill.created_date) == nam)

    if ma_bac_si:
        query = query.filter(Appointment.doctor_id == ma_bac_si)
    return query.group_by(func.date(Bill.created_date)).order_by('ngay').all()
