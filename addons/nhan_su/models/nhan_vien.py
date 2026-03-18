# -*- coding: utf-8 -*-
from odoo import models, fields, api
import hashlib


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_ten'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ma_dinh_danh = fields.Char("Mã định danh", required=True, copy=False,
                                default=lambda self: self.env['ir.sequence'].next_by_code('nhan_vien') or 'NV/001')
    ho_ten = fields.Char("Họ tên", required=True, default='', tracking=True)
    gioi_tinh = fields.Selection([('nam', 'Nam'), ('nu', 'Nữ'), ('khac', 'Khác')], string="Giới tính", default='nam')
    ngay_sinh = fields.Date("Ngày sinh")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    que_quan = fields.Char("Quê quán")
    dia_chi = fields.Char("Địa chỉ thường trú")
    anh_dai_dien = fields.Binary("Ảnh đại diện", attachment=True)
    so_cmnd = fields.Char("Số CMND/CCCD")
    ngay_cap_cmnd = fields.Date("Ngày cấp")
    noi_cap_cmnd = fields.Char("Nơi cấp")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    trang_thai = fields.Selection([
        ('dang_lam', 'Đang làm việc'),
        ('thu_viec', 'Đang thử việc'),
        ('nghi_thai_san', 'Nghỉ thai sản'),
        ('nghi_viec', 'Đã nghỉ việc'),
    ], string="Trạng thái", default='dang_lam', tracking=True)
    ngay_vao_lam = fields.Date("Ngày vào làm")
    ngay_nghi_viec = fields.Date("Ngày nghỉ việc")
    tham_nien = fields.Integer("Thâm niên (năm)", compute="_compute_tham_nien", store=True)
    phong_ban_hien_tai = fields.Many2one('phong_ban', string="Phòng ban hiện tại",
                                          compute='_compute_vi_tri_hien_tai', store=True)
    chuc_vu_hien_tai = fields.Many2one('chuc_vu', string="Chức vụ hiện tại",
                                        compute='_compute_vi_tri_hien_tai', store=True)
    so_tai_khoan = fields.Char("Số tài khoản ngân hàng")
    ngan_hang = fields.Char("Ngân hàng")
    ma_so_thue = fields.Char("Mã số thuế cá nhân")
    so_nguoi_phu_thuoc = fields.Integer("Số người phụ thuộc", default=0)
    lich_su_cong_tac_ids = fields.One2many("lich_su_cong_tac", string="Lịch sử công tác", inverse_name="nhan_vien_id")
    hop_dong_ids = fields.One2many("hop_dong_lao_dong", string="Hợp đồng lao động", inverse_name="nhan_vien_id")
    cham_cong_ids = fields.One2many("cham_cong", string="Chấm công", inverse_name="nhan_vien_id")
    bang_luong_ids = fields.One2many("bang_luong", string="Bảng lương", inverse_name="nhan_vien_id")
    kpi_ids = fields.One2many("kpi_nhan_vien", string="Đánh giá KPI", inverse_name="nhan_vien_id")
    user_id = fields.Many2one('res.users', string='Tài khoản Odoo', ondelete='set null')
    web_username = fields.Char("Tên đăng nhập web")
    web_password_hash = fields.Char("Mật khẩu (hash)")
    is_web_active = fields.Boolean("Kích hoạt web", default=False)
    last_login = fields.Datetime("Đăng nhập lần cuối")

    @api.depends('ngay_sinh')
    def _compute_tuoi(self):
        for r in self:
            r.tuoi = (fields.Date.today() - r.ngay_sinh).days // 365 if r.ngay_sinh else 0

    @api.depends('ngay_vao_lam')
    def _compute_tham_nien(self):
        for r in self:
            r.tham_nien = (fields.Date.today() - r.ngay_vao_lam).days // 365 if r.ngay_vao_lam else 0

    @api.depends('lich_su_cong_tac_ids', 'lich_su_cong_tac_ids.time_start')
    def _compute_vi_tri_hien_tai(self):
        for r in self:
            if r.lich_su_cong_tac_ids:
                latest = r.lich_su_cong_tac_ids.sorted('time_start', reverse=True)[0]
                r.phong_ban_hien_tai = latest.phong_ban_id
                r.chuc_vu_hien_tai = latest.chuc_vu_id
            else:
                r.phong_ban_hien_tai = False
                r.chuc_vu_hien_tai = False

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    @api.model
    def web_login(self, username, password):
        employee = self.sudo().search([
            ('web_username', '=', username),
            ('web_password_hash', '=', self._hash_password(password)),
            ('is_web_active', '=', True)
        ], limit=1)
        if not employee:
            return {'success': False, 'message': 'Tên đăng nhập hoặc mật khẩu không đúng'}
        employee.sudo().write({'last_login': fields.Datetime.now()})
        return {'success': True, 'employee': {'id': employee.id, 'ho_ten': employee.ho_ten}}
