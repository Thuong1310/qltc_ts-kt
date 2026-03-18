# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class HopDongLaoDong(models.Model):
    _name = 'hop_dong_lao_dong'
    _description = 'Hợp đồng lao động'
    _rec_name = 'so_hop_dong'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    so_hop_dong = fields.Char("Số hợp đồng", required=True, copy=False,
                               default=lambda self: self.env['ir.sequence'].next_by_code('hop_dong_lao_dong') or 'HĐ/001')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban")
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ")

    loai_hop_dong = fields.Selection([
        ('thu_viec', 'Thử việc'),
        ('chinh_thuc', 'Chính thức'),
        ('thoi_vu', 'Thời vụ'),
        ('khong_xac_dinh', 'Không xác định thời hạn'),
    ], string="Loại hợp đồng", required=True, default='chinh_thuc', tracking=True)

    ngay_ky = fields.Date("Ngày ký", required=True, default=fields.Date.today)
    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True, default=fields.Date.today)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")

    luong_co_ban = fields.Float("Lương cơ bản (VNĐ)", required=True, default=0.0)
    phu_cap_chuc_vu = fields.Float("Phụ cấp chức vụ (VNĐ)", default=0.0)
    phu_cap_di_lai = fields.Float("Phụ cấp đi lại (VNĐ)", default=0.0)
    phu_cap_an_trua = fields.Float("Phụ cấp ăn trưa (VNĐ)", default=0.0)
    tong_thu_nhap = fields.Float("Tổng thu nhập", compute='_compute_tong_thu_nhap', store=True)

    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('hieu_luc', 'Có hiệu lực'),
        ('het_han', 'Hết hạn'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', tracking=True)

    ghi_chu = fields.Text("Ghi chú")
    nguoi_ky_id = fields.Many2one('res.users', string="Người ký", default=lambda self: self.env.user)

    con_hieu_luc = fields.Boolean("Còn hiệu lực", compute='_compute_con_hieu_luc', store=True)

    @api.depends('luong_co_ban', 'phu_cap_chuc_vu', 'phu_cap_di_lai', 'phu_cap_an_trua')
    def _compute_tong_thu_nhap(self):
        for r in self:
            r.tong_thu_nhap = r.luong_co_ban + r.phu_cap_chuc_vu + r.phu_cap_di_lai + r.phu_cap_an_trua

    @api.depends('trang_thai', 'ngay_ket_thuc')
    def _compute_con_hieu_luc(self):
        today = date.today()
        for r in self:
            if r.trang_thai == 'hieu_luc':
                if r.ngay_ket_thuc:
                    r.con_hieu_luc = r.ngay_ket_thuc >= today
                else:
                    r.con_hieu_luc = True
            else:
                r.con_hieu_luc = False

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for r in self:
            if r.ngay_ket_thuc and r.ngay_bat_dau > r.ngay_ket_thuc:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    def action_ky_hop_dong(self):
        self.write({'trang_thai': 'hieu_luc'})

    def action_huy_hop_dong(self):
        self.write({'trang_thai': 'huy'})

    def action_gia_han(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gia hạn hợp đồng',
            'res_model': 'hop_dong_lao_dong',
            'view_mode': 'form',
            'context': {
                'default_nhan_vien_id': self.nhan_vien_id.id,
                'default_loai_hop_dong': self.loai_hop_dong,
                'default_luong_co_ban': self.luong_co_ban,
                'default_chuc_vu_id': self.chuc_vu_id.id,
            },
            'target': 'new',
        }
