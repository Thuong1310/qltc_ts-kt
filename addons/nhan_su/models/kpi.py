# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KpiDotDanhGia(models.Model):
    _name = 'kpi_dot_danh_gia'
    _description = 'Đợt đánh giá KPI'
    _rec_name = 'ten_dot'

    ten_dot = fields.Char("Tên đợt đánh giá", required=True)
    ky_danh_gia = fields.Selection([
        ('thang', 'Theo tháng'),
        ('quy', 'Theo quý'),
        ('nam', 'Theo năm'),
    ], string="Kỳ đánh giá", required=True, default='quy')
    tu_ngay = fields.Date("Từ ngày", required=True)
    den_ngay = fields.Date("Đến ngày", required=True)
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
    ], string="Trạng thái", default='nhap')
    mo_ta = fields.Text("Mô tả")
    kpi_ids = fields.One2many('kpi_nhan_vien', 'dot_danh_gia_id', string="KPI nhân viên")
    tong_nhan_vien = fields.Integer("Tổng NV được đánh giá", compute='_compute_tong_nv')

    @api.depends('kpi_ids')
    def _compute_tong_nv(self):
        for r in self:
            r.tong_nhan_vien = len(r.kpi_ids)

    def action_bat_dau(self):
        self.write({'trang_thai': 'dang_thuc_hien'})

    def action_hoan_thanh(self):
        self.write({'trang_thai': 'hoan_thanh'})


class KpiNhanVien(models.Model):
    _name = 'kpi_nhan_vien'
    _description = 'Đánh giá KPI nhân viên'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    dot_danh_gia_id = fields.Many2one('kpi_dot_danh_gia', string="Đợt đánh giá", required=True, ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban")
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ")
    display_name = fields.Char("Tên", compute='_compute_display_name', store=True)

    # Tiêu chí đánh giá
    tieu_chi_ids = fields.One2many('kpi_tieu_chi', 'kpi_nhan_vien_id', string="Tiêu chí KPI")

    # Tổng điểm
    diem_tu_danh_gia = fields.Float("Điểm tự đánh giá", compute='_compute_diem', store=True)
    diem_quan_ly_danh_gia = fields.Float("Điểm quản lý đánh giá", compute='_compute_diem', store=True)
    diem_tong_hop = fields.Float("Điểm tổng hợp", compute='_compute_diem', store=True)

    xep_loai = fields.Selection([
        ('xuat_sac', 'Xuất sắc (≥90)'),
        ('tot', 'Tốt (75-89)'),
        ('kha', 'Khá (60-74)'),
        ('trung_binh', 'Trung bình (50-59)'),
        ('kem', 'Kém (<50)'),
    ], string="Xếp loại", compute='_compute_xep_loai', store=True)

    trang_thai = fields.Selection([
        ('chua_danh_gia', 'Chưa đánh giá'),
        ('nhan_vien_da_nhap', 'NV đã nhập'),
        ('quan_ly_da_nhap', 'QL đã nhập'),
        ('hoan_thanh', 'Hoàn thành'),
    ], string="Trạng thái", default='chua_danh_gia', tracking=True)

    nhan_xet_nhan_vien = fields.Text("Nhận xét của nhân viên")
    nhan_xet_quan_ly = fields.Text("Nhận xét của quản lý")

    @api.depends('nhan_vien_id', 'dot_danh_gia_id')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_ten if r.nhan_vien_id else ''
            dot = r.dot_danh_gia_id.ten_dot if r.dot_danh_gia_id else ''
            r.display_name = f"{nv} - {dot}"

    @api.depends('tieu_chi_ids.diem_tu_danh_gia', 'tieu_chi_ids.diem_quan_ly', 'tieu_chi_ids.trong_so')
    def _compute_diem(self):
        for r in self:
            tong_trong_so = sum(tc.trong_so for tc in r.tieu_chi_ids)
            if tong_trong_so > 0:
                r.diem_tu_danh_gia = sum(
                    tc.diem_tu_danh_gia * tc.trong_so for tc in r.tieu_chi_ids) / tong_trong_so
                r.diem_quan_ly_danh_gia = sum(
                    tc.diem_quan_ly * tc.trong_so for tc in r.tieu_chi_ids) / tong_trong_so
                r.diem_tong_hop = (r.diem_tu_danh_gia * 0.3 + r.diem_quan_ly_danh_gia * 0.7)
            else:
                r.diem_tu_danh_gia = 0
                r.diem_quan_ly_danh_gia = 0
                r.diem_tong_hop = 0

    @api.depends('diem_tong_hop')
    def _compute_xep_loai(self):
        for r in self:
            d = r.diem_tong_hop
            if d >= 90:
                r.xep_loai = 'xuat_sac'
            elif d >= 75:
                r.xep_loai = 'tot'
            elif d >= 60:
                r.xep_loai = 'kha'
            elif d >= 50:
                r.xep_loai = 'trung_binh'
            else:
                r.xep_loai = 'kem'


class KpiTieuChi(models.Model):
    _name = 'kpi_tieu_chi'
    _description = 'Tiêu chí KPI'

    kpi_nhan_vien_id = fields.Many2one('kpi_nhan_vien', string="KPI nhân viên", required=True, ondelete='cascade')
    ten_tieu_chi = fields.Char("Tên tiêu chí", required=True)
    mo_ta = fields.Text("Mô tả / Mục tiêu")
    trong_so = fields.Float("Trọng số (%)", default=20.0)
    muc_tieu = fields.Char("Mục tiêu")
    ket_qua_thuc_te = fields.Char("Kết quả thực tế")
    diem_tu_danh_gia = fields.Float("Điểm tự đánh giá (0-100)", default=0.0)
    diem_quan_ly = fields.Float("Điểm quản lý (0-100)", default=0.0)
    nhan_xet = fields.Char("Nhận xét")

    @api.constrains('trong_so')
    def _check_trong_so(self):
        for r in self:
            if r.trong_so < 0 or r.trong_so > 100:
                raise ValidationError("Trọng số phải từ 0 đến 100!")

    @api.constrains('diem_tu_danh_gia', 'diem_quan_ly')
    def _check_diem(self):
        for r in self:
            if not (0 <= r.diem_tu_danh_gia <= 100):
                raise ValidationError("Điểm tự đánh giá phải từ 0 đến 100!")
            if not (0 <= r.diem_quan_ly <= 100):
                raise ValidationError("Điểm quản lý phải từ 0 đến 100!")
