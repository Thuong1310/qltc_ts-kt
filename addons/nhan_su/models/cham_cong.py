# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time


class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bảng chấm công'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    ngay = fields.Date("Ngày", required=True, default=fields.Date.today)
    gio_vao = fields.Float("Giờ vào", help="Nhập giờ theo định dạng thập phân (VD: 8.5 = 8:30)")
    gio_ra = fields.Float("Giờ ra")
    so_gio_lam = fields.Float("Số giờ làm", compute='_compute_so_gio', store=True)
    so_gio_tang_ca = fields.Float("Tăng ca (giờ)", default=0.0)

    loai_cong = fields.Selection([
        ('di_lam', 'Đi làm'),
        ('nghi_phep', 'Nghỉ phép'),
        ('nghi_le', 'Nghỉ lễ'),
        ('nghi_om', 'Nghỉ ốm'),
        ('nghi_khac', 'Nghỉ khác'),
        ('cong_tac', 'Công tác'),
        ('lam_viec_tu_xa', 'Làm việc từ xa'),
    ], string="Loại công", required=True, default='di_lam', tracking=True)

    trang_thai = fields.Selection([
        ('cho_xac_nhan', 'Chờ xác nhận'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('tu_choi', 'Từ chối'),
    ], string="Trạng thái", default='cho_xac_nhan', tracking=True)

    ghi_chu = fields.Char("Ghi chú")
    display_name = fields.Char("Tên", compute='_compute_display_name', store=True)

    @api.depends('nhan_vien_id', 'ngay')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_ten if r.nhan_vien_id else ''
            ng = r.ngay.strftime('%d/%m/%Y') if r.ngay else ''
            r.display_name = f"{nv} - {ng}"

    @api.depends('gio_vao', 'gio_ra')
    def _compute_so_gio(self):
        for r in self:
            if r.gio_vao and r.gio_ra and r.gio_ra > r.gio_vao:
                r.so_gio_lam = r.gio_ra - r.gio_vao - 1.0  # trừ 1 giờ nghỉ trưa
            else:
                r.so_gio_lam = 0.0

    def action_xac_nhan(self):
        self.write({'trang_thai': 'da_xac_nhan'})

    def action_tu_choi(self):
        self.write({'trang_thai': 'tu_choi'})

    @api.model
    def get_tong_cong_thang(self, nhan_vien_id, nam, thang):
        """Tính tổng công của nhân viên trong tháng"""
        records = self.search([
            ('nhan_vien_id', '=', nhan_vien_id),
            ('ngay', '>=', f'{nam}-{thang:02d}-01'),
            ('ngay', '<=', f'{nam}-{thang:02d}-31'),
            ('trang_thai', '=', 'da_xac_nhan'),
            ('loai_cong', '=', 'di_lam'),
        ])
        return len(records)


class NghiPhep(models.Model):
    _name = 'nghi_phep'
    _description = 'Đơn xin nghỉ phép'
    _rec_name = 'so_don'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    so_don = fields.Char("Số đơn", copy=False,
                          default=lambda self: self.env['ir.sequence'].next_by_code('nghi_phep') or 'NP/001')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    loai_nghi = fields.Selection([
        ('phep_nam', 'Phép năm'),
        ('phep_om', 'Nghỉ ốm'),
        ('phep_thai_san', 'Thai sản'),
        ('phep_khong_luong', 'Không lương'),
        ('nghi_le', 'Nghỉ lễ'),
        ('viec_rieng', 'Việc riêng'),
    ], string="Loại nghỉ", required=True, default='phep_nam')

    tu_ngay = fields.Date("Từ ngày", required=True, default=fields.Date.today)
    den_ngay = fields.Date("Đến ngày", required=True, default=fields.Date.today)
    so_ngay_nghi = fields.Float("Số ngày nghỉ", compute='_compute_so_ngay', store=True)
    ly_do = fields.Text("Lý do", required=True)

    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('tu_choi', 'Từ chối'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', tracking=True)

    nguoi_duyet_id = fields.Many2one('res.users', string="Người duyệt", readonly=True)
    ngay_duyet = fields.Datetime("Ngày duyệt", readonly=True)
    ly_do_tu_choi = fields.Text("Lý do từ chối")

    @api.depends('tu_ngay', 'den_ngay')
    def _compute_so_ngay(self):
        for r in self:
            if r.tu_ngay and r.den_ngay and r.den_ngay >= r.tu_ngay:
                delta = (r.den_ngay - r.tu_ngay).days + 1
                r.so_ngay_nghi = delta
            else:
                r.so_ngay_nghi = 0

    @api.constrains('tu_ngay', 'den_ngay')
    def _check_dates(self):
        for r in self:
            if r.den_ngay and r.tu_ngay > r.den_ngay:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    def action_gui_don(self):
        self.write({'trang_thai': 'cho_duyet'})

    def action_duyet(self):
        self.write({
            'trang_thai': 'da_duyet',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now(),
        })

    def action_tu_choi(self):
        self.write({'trang_thai': 'tu_choi'})

    def action_huy(self):
        self.write({'trang_thai': 'huy'})
