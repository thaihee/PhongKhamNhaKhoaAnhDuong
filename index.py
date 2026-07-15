from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from matplotlib.ticker import FuncFormatter
from PhongKhamNhaKhoa import app, db, login_manager, dao
from PhongKhamNhaKhoa.models import User, Appointment, UserRole, Gender, PatientProfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

@app.route("/")
def index():
    if current_user.is_authenticated and current_user.role == UserRole.STAFF:
        appointments = dao.get_appointments_by_status('Chờ thanh toán')
    else:
        appointments = dao.get_all_appointments()
    return render_template('index.html', appointments=appointments)

@app.route('/login', methods=['get', 'post'])
def login():
    err_msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username, password)
        if user:
            login_user(user)
            next = request.args.get("next")
            return redirect(next if next else '/')
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("login.html", err_msg=err_msg)

@app.route("/register", methods=['get', 'post'])
def register():
    err_msg = None
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password != confirm:
            err_msg = "Mật khẩu không khớp!"
        else:
            fullname = request.form.get('fullname')
            username = request.form.get('username')
            dob = request.form.get('dob')
            gender_str = request.form.get('gender')

            gender =Gender[gender_str]
            try:
                dao.add_user(fullname, username, password, dob, gender)
                return redirect('/login')
            except:
                db.session.rollback()
                err_msg = "Hệ thống đang bị lỗi! Vui lòng quay lại sau!"
    return render_template('register.html', err_msg=err_msg)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/dangkylichkham", methods=['get', 'post'])
@login_required
def register_appointment():
    err_msg = None
    if request.method == 'POST':
        phone = request.form.get('phone')
        time_slot = request.form.get('time_slot')
        date_input = request.form.get('date')
        doctor_id = request.form.get('doctor_id')
        service_type = request.form.get('service_type')
        success, msg = dao.add_appointment(
            user_id=current_user.id,
            name=current_user.fullname,
            time_slot=time_slot,
            phone=phone,
            date_str=date_input,
            doctor_id=doctor_id,
            service_type=service_type
        )
        if success:
            flash("Đăng ký thành công!", "success")
            return redirect(url_for('register_appointment'))
        else:
            err_msg = msg
    doctors = dao.get_all_doctors()
    services = dao.get_services()
    return render_template('dangkylichkham.html', doctors=doctors, services=services, err_msg=err_msg)

@app.route("/doctor/appointments")
@login_required
def appointment_list():
    doctor = dao.get_doctor_by_user_id(current_user.id)
    d_str = request.args.get('date')
    if d_str:
        d = datetime.strptime(d_str, '%Y-%m-%d').date()
    else:
        d = date.today()
    appointments = dao.get_appointments_by_doctor(doctor.id, d)
    return render_template('appointment_list.html', appointments=appointments, selected_date=d)


@app.route("/treatment/<int:appointment_id>", methods=['GET', 'POST'])
def treatment(appointment_id):
    appo = Appointment.query.get(appointment_id)

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        treatment_note = request.form.get('treatment_note')
        service_ids = request.form.getlist('service_id')
        selectedKeDon = request.form.get('selectedKeDon')

        ts = dao.add_treatment_record(
            appointment_id=appointment_id,
            diagnosis=diagnosis,
            service_ids=service_ids,
            note=treatment_note
        )

        if ts:
            new_status = "Chờ kê đơn" if selectedKeDon else "Chờ thanh toán"
            dao.update_appointment_status(appointment_id, new_status)
            flash("Đã lưu nội dung điều trị!", "success")
            return redirect(url_for('appointment_list'))

    services = dao.get_services()
    return render_template('treatment.html', appo=appo, services=services)

@app.route("/prescription/<int:treatment_id>", methods=['GET', 'POST'])
@login_required
def prescription(treatment_id):
    ts = dao.get_treament_sheet_by_id(treatment_id)
    if not ts:
        flash("Không tìm thấy phiếu điều trị!", "danger")
        return redirect(url_for('appointment_list'))

    if request.method == 'POST':
        medicine_ids = request.form.getlist('medicine_id')
        dosages = request.form.getlist('dosage')
        units = request.form.getlist('unit')
        days_list = request.form.getlist('days')
        med_notes = request.form.getlist('med_note')
        for i in range(len(medicine_ids)):
            if medicine_ids[i]:
                dao.add_prescription_detail(treatment_id, int(medicine_ids[i]), dosages[i], units[i], days_list[i], med_notes[i])
        dao.update_appointment_status(ts.appointment_id, "Chờ thanh toán")
        flash("Đã lưu đơn thuốc thành công!", "success")
        return redirect(url_for('appointment_list'))
    medicines = dao.get_medicines()
    return render_template('prescription.html', ts=ts, medicines=medicines)

@app.route("/pending_payments")
@login_required
def pending_payments():
    if current_user.role != UserRole.STAFF:
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('index'))

    appointments = dao.get_appointments_by_status(status='Chờ thanh toán')
    return render_template('pending_payments.html', appointments=appointments)


@app.route("/payment/<int:treatment_id>", methods=['GET', 'POST'])
def payment(treatment_id):
    coupon_code = request.args.get('coupon_code')
    data = dao.get_bill_details(treatment_id, coupon_code)

    if request.method == 'POST':
        staff_obj = current_user.staff_profile
        st_id = staff_obj.id if staff_obj else None

        appo = data['ts'].appointment
        patient = appo.patient

        if not patient.profile:
            new_profile = PatientProfile(patient_id=patient.id)
            db.session.add(new_profile)
            db.session.flush()
            pr_id = new_profile.id
        else:
            pr_id = patient.profile.id

        if st_id is None:
            flash("Lỗi: Bạn phải đăng nhập bằng tài khoản NHÂN VIÊN để thanh toán!", "danger")
            return redirect(url_for('pending_payments'))

        success = dao.confirm_payment(
            appointment_id=appo.id,
            service_fee=data['service_total'],
            medicine_fee=data['medicine_total'],
            discount=data['discount_amount'],
            total_amount=data['total_amount'],
            staff_id=st_id,
            profile_id=pr_id,
            coupon_id=data['coupon_obj'].id if data['coupon_obj'] else None
        )

        if success:
            flash("Thanh toán thành công!", "success")
            return redirect(url_for('pending_payments'))
        else:
            flash("Lỗi hệ thống khi lưu hóa đơn!", "danger")

    return render_template('payment.html', **data, coupon=data['coupon_obj'], current_time=datetime.now())


@app.route("/thongke")
def trang_thong_ke():
    thang = request.args.get('thang', datetime.now().month)
    nam = request.args.get('nam', datetime.now().year)
    ma_bs = request.args.get('ma_bac_si')

    ds_bac_si = dao.lay_danh_sach_bac_si()
    du_lieu = dao.thong_ke_doanh_thu(int(thang), int(nam), ma_bs)

    tong_cong = sum(d[1] for d in du_lieu) if du_lieu else 0

    bieu_do_final = ""
    if du_lieu:
        ngay = [d[0].strftime('%d/%m') for d in du_lieu]
        tien = [d[1] for d in du_lieu]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(ngay, tien, color='#0d6efd', alpha=0.8)

        def vnd_formatter(x, pos):
            return f'{x:,.0f}'

        ax.get_yaxis().set_major_formatter(FuncFormatter(vnd_formatter))

        ax.set_title(f'BIỂU ĐỒ DOANH THU {thang}/{nam}', fontsize=12, fontweight='bold')
        ax.set_ylabel('Số tiền (VNĐ)')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        bieu_do_final = base64.b64encode(buf.getvalue()).decode()
        plt.close(fig)

    return render_template('stats.html',
                           bieu_do=bieu_do_final,
                           tong_tien=tong_cong,
                           doctors=ds_bac_si,
                           month=int(thang),
                           year=int(nam),
                           selected_doc=ma_bs)

if __name__ == '__main__':
    app.run(debug=True)