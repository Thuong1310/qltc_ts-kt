# Hướng Dẫn Cài Đặt - TechCorp Business System

## Yêu Cầu Hệ Thống

- **Odoo**: 17.0 Community hoặc Enterprise
- **Python**: 3.10+
- **PostgreSQL**: 14+
- **Trình duyệt**: Chrome 90+, Firefox 88+, Edge 90+

## Bước 1: Sao Chép Module

```bash
# Sao chép toàn bộ thư mục addons vào đường dẫn addons của Odoo
cp -r business_system/addons/* /path/to/odoo/custom_addons/

# Cấu trúc sau khi sao chép:
# custom_addons/
# ├── nhan_su/
# ├── quan_ly_tai_chinh/
# ├── quan_ly_tai_san/
# └── upgrade_project/
```

## Bước 2: Cấu Hình addons_path

Trong file `odoo.conf`:
```ini
addons_path = /path/to/odoo/addons,/path/to/custom_addons
```

## Bước 3: Restart Odoo

```bash
sudo systemctl restart odoo
# hoặc
python3 odoo-bin -c odoo.conf
```

## Bước 4: Cài Đặt Module (theo thứ tự)

1. Vào **Settings → Apps**
2. Tắt filter "Apps" để hiện tất cả module
3. Cài đặt theo thứ tự:
   - `Quản Lý Nhân Sự - TechCorp` (nhan_su)
   - `Quản Lý Tài Chính Kế Toán - TechCorp` (quan_ly_tai_chinh)
   - `Quản Lý Tài Sản - TechCorp` (quan_ly_tai_san)
   - `TechCorp Dashboard Tổng Hợp` (upgrade_project)

## Bước 5: Kiểm Tra Sau Cài Đặt

- ✅ Menu **👥 Nhân Sự** xuất hiện
- ✅ Menu **💰 Tài Chính - Kế Toán** xuất hiện
- ✅ Menu **🏢 Tài Sản** xuất hiện
- ✅ Menu **📊 Dashboard** xuất hiện
- ✅ 12 tài khoản kế toán đã được tạo tự động
- ✅ 5 loại tài sản mặc định đã được tạo

## Xử Lý Lỗi Thường Gặp

### Lỗi: "Module not found"
```bash
# Cập nhật danh sách module
python3 odoo-bin -c odoo.conf -u base --stop-after-init
```

### Lỗi: "Dependency missing"
Đảm bảo cài đúng thứ tự: nhan_su → quan_ly_tai_chinh → quan_ly_tai_san → upgrade_project

### Lỗi: Chart.js không hiển thị
Kiểm tra kết nối internet (Chart.js load từ CDN). Nếu không có internet, tải Chart.js về và đặt vào `static/lib/`.
