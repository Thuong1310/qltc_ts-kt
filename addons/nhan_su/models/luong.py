# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BangLuong(models.Model):
    _name = 'bang_luong'
    _description = 'Bảng tính lương'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    display_name = fields.Char("Tên", compute='_compute_display_name', store=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True, ondelete='cascade')
    thang = fields.Integer("Tháng", required=True)
    nam = fields.Integer("Năm", required=True, default=lambda self: fields.Date.today().year)

    # Lương cơ bản từ hợp đồng
    luong_co_ban = fields.Float("Lương cơ bản", required=True)
    phu_cap_chuc_vu = fields.Float("Phụ cấp chức vụ", default=0.0)
    phu_cap_di_lai = fields.Float("Phụ cấp đi lại", default=0.0)
    phu_cap_an_trua = fields.Float("Phụ cấp ăn trưa", default=0.0)

    # Công
    so_ngay_cong_chuan = fields.Float("Ngày công chuẩn", default=26.0)
    so_ngay_cong_thuc_te = fields.Float("Ngày công thực tế", default=0.0)
    so_gio_tang_ca = fields.Float("Giờ tăng ca", default=0.0)
    he_so_tang_ca = fields.Float("Hệ số tăng ca", default=1.5)

    # Thưởng
    thuong_hieu_qua = fields.Float("Thưởng hiệu quả", default=0.0)
    thuong_chuyem_can = fields.Float("Thưởng chuyên cần", default=0.0)
    thuong_khac = fields.Float("Thưởng khác", default=0.0)

    # Khấu trừ
    bao_hiem_xa_hoi = fields.Float("BHXH (8%)", compute='_compute_bao_hiem', store=True)
    bao_hiem_y_te = fields.Float("BHYT (1.5%)", compute='_compute_bao_hiem', store=True)
    bao_hiem_that_nghiep = fields.Float("BHTN (1%)", compute='_compute_bao_hiem', store=True)
    tam_ung = fields.Float("Tạm ứng", default=0.0)
    khau_tru_khac = fields.Float("Khấu trừ khác", default=0.0)

    # Tổng
    tong_thu_nhap_truoc_thue = fields.Float("Tổng TN trước thuế", compute='_compute_tong', store=True)
    thue_tncn = fields.Float("Thuế TNCN", compute='_compute_thue', store=True)
    luong_thuc_linh = fields.Float("Lương thực lĩnh", compute='_compute_tong', store=True)

    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('da_thanh_toan', 'Đã thanh toán'),
    ], string="Trạng thái", default='nhap', tracking=True)

    ghi_chu = fields.Text("Ghi chú")

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_ten if r.nhan_vien_id else ''
            r.display_name = f"Lương {r.thang:02d}/{r.nam} - {nv}"

    @api.depends('luong_co_ban')
    def _compute_bao_hiem(self):
        for r in self:
            r.bao_hiem_xa_hoi = r.luong_co_ban * 0.08
            r.bao_hiem_y_te = r.luong_co_ban * 0.015
            r.bao_hiem_that_nghiep = r.luong_co_ban * 0.01

    @api.depends('luong_co_ban', 'so_ngay_cong_chuan', 'so_ngay_cong_thuc_te',
                 'phu_cap_chuc_vu', 'phu_cap_di_lai', 'phu_cap_an_trua',
                 'so_gio_tang_ca', 'he_so_tang_ca',
                 'thuong_hieu_qua', 'thuong_chuyem_can', 'thuong_khac',
                 'bao_hiem_xa_hoi', 'bao_hiem_y_te', 'bao_hiem_that_nghiep',
                 'tam_ung', 'khau_tru_khac', 'thue_tncn')
    def _compute_tong(self):
        for r in self:
            # Lương theo ngày công
            if r.so_ngay_cong_chuan > 0:
                luong_thuc_te = r.luong_co_ban * (r.so_ngay_cong_thuc_te / r.so_ngay_cong_chuan)
            else:
                luong_thuc_te = r.luong_co_ban

            # Lương tăng ca
            don_gia_gio = r.luong_co_ban / (r.so_ngay_cong_chuan * 8) if r.so_ngay_cong_chuan else 0
            luong_tang_ca = don_gia_gio * r.so_gio_tang_ca * r.he_so_tang_ca

            # Tổng thu nhập
            tong_phu_cap = r.phu_cap_chuc_vu + r.phu_cap_di_lai + r.phu_cap_an_trua
            tong_thuong = r.thuong_hieu_qua + r.thuong_chuyem_can + r.thuong_khac
            r.tong_thu_nhap_truoc_thue = luong_thuc_te + luong_tang_ca + tong_phu_cap + tong_thuong

            # Tổng khấu trừ
            tong_khau_tru = (r.bao_hiem_xa_hoi + r.bao_hiem_y_te + r.bao_hiem_that_nghiep +
                             r.tam_ung + r.khau_tru_khac + r.thue_tncn)
            r.luong_thuc_linh = r.tong_thu_nhap_truoc_thue - tong_khau_tru

    @api.depends('tong_thu_nhap_truoc_thue', 'bao_hiem_xa_hoi', 'bao_hiem_y_te', 'bao_hiem_that_nghiep')
    def _compute_thue(self):
        for r in self:
            # Thu nhập chịu thuế = Tổng TN - BHXH - BHYT - BHTN - Giảm trừ bản thân (11tr/tháng)
            giam_tru_ban_than = 11_000_000
            thu_nhap_chiu_thue = (r.tong_thu_nhap_truoc_thue
                                  - r.bao_hiem_xa_hoi - r.bao_hiem_y_te - r.bao_hiem_that_nghiep
                                  - giam_tru_ban_than)
            if thu_nhap_chiu_thue <= 0:
                r.thue_tncn = 0
            elif thu_nhap_chiu_thue <= 5_000_000:
                r.thue_tncn = thu_nhap_chiu_thue * 0.05
            elif thu_nhap_chiu_thue <= 10_000_000:
                r.thue_tncn = 250_000 + (thu_nhap_chiu_thue - 5_000_000) * 0.10
            elif thu_nhap_chiu_thue <= 18_000_000:
                r.thue_tncn = 750_000 + (thu_nhap_chiu_thue - 10_000_000) * 0.15
            elif thu_nhap_chiu_thue <= 32_000_000:
                r.thue_tncn = 1_950_000 + (thu_nhap_chiu_thue - 18_000_000) * 0.20
            else:
                r.thue_tncn = 4_750_000 + (thu_nhap_chiu_thue - 32_000_000) * 0.25

    def action_gui_duyet(self):
        self.write({'trang_thai': 'cho_duyet'})

    def action_duyet(self):
        self.write({'trang_thai': 'da_duyet'})

    def action_thanh_toan(self):
        self.write({'trang_thai': 'da_thanh_toan'})

    @api.model
    def tao_bang_luong_tu_hop_dong(self, nhan_vien_id, thang, nam):
        """Tạo bảng lương tự động từ hợp đồng đang hiệu lực"""
        hop_dong = self.env['hop_dong_lao_dong'].search([
            ('nhan_vien_id', '=', nhan_vien_id),
            ('trang_thai', '=', 'hieu_luc'),
        ], limit=1, order='ngay_bat_dau desc')

        vals = {
            'nhan_vien_id': nhan_vien_id,
            'thang': thang,
            'nam': nam,
        }
        if hop_dong:
            vals.update({
                'luong_co_ban': hop_dong.luong_co_ban,
                'phu_cap_chuc_vu': hop_dong.phu_cap_chuc_vu,
                'phu_cap_di_lai': hop_dong.phu_cap_di_lai,
                'phu_cap_an_trua': hop_dong.phu_cap_an_trua,
            })
        return self.create(vals)
