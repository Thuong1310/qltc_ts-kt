# Checklist Triển Khai - TechCorp Business System

## ✅ Pre-Installation

- [ ] Odoo 17.0 đã cài đặt và chạy
- [ ] PostgreSQL đang hoạt động
- [ ] Backup database hiện tại (nếu có)
- [ ] Kiểm tra phiên bản Python ≥ 3.10

## ✅ Module Files

### nhan_su
- [ ] 10 Python models có trong `models/`
- [ ] 11 XML view files có trong `views/`
- [ ] `security/ir_model_access.csv` đủ 10 dòng access rules
- [ ] `data/sequence_data.xml` có sequence NV, PB, HĐ
- [ ] `controllers/` có `__init__.py` và `controllers.py`

### quan_ly_tai_chinh
- [ ] 7 Python models có trong `models/`
- [ ] 9 XML view files (bao gồm `tai_chinh_tree_views.xml`)
- [ ] `security/ir_model_access.csv` đủ 7 dòng
- [ ] `data/tai_khoan_data.xml` có 12 tài khoản + 2 sequences
- [ ] `controllers/` có API endpoints

### quan_ly_tai_san
- [ ] 10 Python models có trong `models/`
- [ ] 9 XML view files (bao gồm `tai_san_tree_views.xml`)
- [ ] `security/ir_model_access.csv` đủ 10 dòng
- [ ] `data/loai_tai_san_data.xml` có 5 loại TS mặc định
- [ ] `data/sequence_data.xml` có sequence TS, MS

### upgrade_project
- [ ] `models/dashboard_tong_hop.py` (~450 dòng)
- [ ] `static/src/js/dashboard_tong_hop.js` (~550 dòng)
- [ ] `static/src/css/dashboard_tong_hop.css` (~400 dòng)
- [ ] `static/src/xml/dashboard_tong_hop.xml` (~300 dòng)
- [ ] `views/assets.xml` có client action
- [ ] `security/ir_model_access.csv`

## ✅ Post-Installation

- [ ] 12 tài khoản kế toán tự động tạo (111, 112, 131, 211, 214, 331, 334, 338, 511, 6274, 6421, 811)
- [ ] 5 loại tài sản mặc định tạo (CNTT, MMT, PT, NVP, DAT)
- [ ] Dashboard hiển thị đúng (menu 📊)
- [ ] Tạo thử nhân viên → ký hợp đồng → phê duyệt → kiểm tra bút toán tự tạo
- [ ] Tạo thử TSCĐ → đưa vào SD → kiểm tra lịch KH tự tạo

## ✅ Automation Workflows Test

- [ ] `ns.bang_luong.action_phe_duyet()` → `qtc.but_toan` tạo tự động ✓
- [ ] `qts.tai_san.action_dua_vao_su_dung()` → `qts.khau_hao` nhiều kỳ tạo tự động ✓
- [ ] `qts.khau_hao.action_ghi_so()` → `qtc.but_toan` tạo + ghi sổ tự động ✓
- [ ] `qts.mua_sam.action_gd_duyet()` → `qtc.but_toan` tạo tự động ✓
- [ ] `qts.mua_sam.action_xac_nhan_mua()` → `qts.tai_san` tạo tự động ✓
- [ ] `ns.nhan_vien.action_nghi_viec()` → thu hồi TS + chấm dứt HĐ ✓
