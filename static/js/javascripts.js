//Đăng ký lịch khám
var today = new Date().toISOString().split('T')[0];
    document.getElementById('date_picker').setAttribute('min', today);

//Lập hóa đơn thanh toán
function applyCoupon() {
    const code = document.getElementById('coupon_input').value.trim(); // Thêm trim()
    const url = new URL(window.location.href);
    if (code) {
        url.searchParams.set('coupon_code', code);
    } else {
        url.searchParams.delete('coupon_code');
    }
    window.location.href = url.toString();
}

//Phiếu điều trị
function addService() {
    const container = document.getElementById('service-list');
    const firstRow = container.querySelector('.service-row');
    const newRow = firstRow.cloneNode(true);
    const select = newRow.querySelector('select');
    select.value = "";
    container.appendChild(newRow);
}

function removeRow(btn) {
    const container = document.getElementById('service-list');
    const rows = container.querySelectorAll('.service-row');
    if (rows.length > 1) {
        btn.closest('.service-row').remove();
    } else {
        alert("Phải có ít nhất một dịch vụ thực hiện.");
    }
}

//Kê đơn thuốc
function addRow() {
        let tableBody = document.querySelector("#prescription-table tbody");
        let firstRow = tableBody.rows[0];
        let newRow = firstRow.cloneNode(true);

        // Reset dữ liệu dòng mới
        newRow.querySelector('select').value = "";
        newRow.querySelectorAll('input').forEach(input => {
            if (input.name === 'med_note' || input.name === 'unit') input.value = "";
            else input.value = "1";
        });

        tableBody.appendChild(newRow);
}

function removeRow(btn) {
    let tableBody = document.querySelector("#prescription-table tbody");
    if (tableBody.rows.length > 1) btn.closest('tr').remove();
    else alert("Đơn thuốc phải có ít nhất một loại thuốc!");
}
