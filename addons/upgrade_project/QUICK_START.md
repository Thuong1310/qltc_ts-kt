# Quick Start Guide - TechCorp Business System

## ⚡ 5 Phút Bắt Đầu

### Bước 1: Tạo Cơ Cấu Tổ Chức (2 phút)
```
Nhân Sự → Cấu Hình → Đơn Vị → Tạo: "Khối Kinh Doanh"
Nhân Sự → Cấu Hình → Phòng Ban → Tạo: "Phòng Kinh Doanh"
Nhân Sự → Cấu Hình → Chức Danh → Tạo: "Nhân Viên Kinh Doanh"
```

### Bước 2: Thêm Nhân Viên (1 phút)
```
Nhân Sự → Nhân Viên → Tạo mới
→ Điền: Họ tên, Phòng ban, Chức danh, Ngày vào làm
→ Lưu (Mã NV tự động: NV0001)
```

### Bước 3: Ký Hợp Đồng → Bút Toán Tự Động (1 phút)
```
Mở hồ sơ NV → Tab Hợp Đồng → Tạo mới
→ Nhập lương cơ bản: 15,000,000 VNĐ
→ Nhấn [✅ Phê Duyệt]
→ 🤖 HỆ THỐNG TỰ ĐỘNG: Tạo bút toán lương
```

### Bước 4: Thêm Tài Sản → Khấu Hao Tự Động (1 phút)
```
Tài Sản → Danh Mục TSCĐ → Tạo mới
→ Tên: "Laptop Dell XPS", Loại: CNTT, Nguyên giá: 25,000,000
→ Nhấn [✅ Đưa Vào Sử Dụng]
→ 🤖 HỆ THỐNG TỰ ĐỘNG: Tạo 36 kỳ khấu hao (3 năm)
```

### Bước 5: Xem Dashboard
```
Menu 📊 Dashboard
→ Xem KPI: NV đang làm, CP lương, GTCL tài sản
→ Xem biểu đồ: Chi phí theo tháng, NV theo PB
```

---

## 🔑 Phím Tắt Quan Trọng

| Thao Tác | Kết Quả Tự Động |
|----------|-----------------|
| Phê duyệt bảng lương | ✅ Bút toán lương |
| Đưa TS vào SD | ✅ Lịch khấu hao N×12 tháng |
| Ghi sổ khấu hao | ✅ Bút toán KH |
| GĐ duyệt mua sắm | ✅ Bút toán mua TS |
| Xác nhận đã mua | ✅ Hồ sơ TSCĐ mới |
| NV nghỉ việc | ✅ Thu hồi TS + chấm dứt HĐ |

---

## 📞 Hỗ Trợ

Xem chi tiết trong thư mục `docs/`:
- `USER_GUIDE.md` - Hướng dẫn sử dụng đầy đủ
- `API_DOCUMENTATION.md` - API reference
- `DEVELOPER_GUIDE.md` - Hướng dẫn phát triển
- `DATABASE_SCHEMA.md` - Sơ đồ cơ sở dữ liệu
