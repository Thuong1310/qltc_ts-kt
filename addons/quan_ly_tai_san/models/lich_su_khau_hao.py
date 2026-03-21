from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class LichSuKhauHao(models.Model):
    _name = 'lich_su_khau_hao'
    _description = 'lich_su_khau_hao'
    _rec_name = "ma_phieu_khau_hao"
    _order = 'ngay_khau_hao desc'
    _sql_constraints = [
        ("ma_phieu_khau_hao_unique", "unique(ma_phieu_khau_hao)", "Mã phiếu khấu hao đã tồn tại !"),
    ]
    
    ma_phieu_khau_hao = fields.Char('Mã phiếu', default='KHTS-', required=True)
    ma_ts = fields.Many2one('tai_san', string='Mã tài sản', required=True, ondelete='cascade')
    ngay_khau_hao = fields.Datetime('Ngày khấu hao',default = fields.Datetime.now(),  required=True)
    gia_tri_hien_tai = fields.Float(string='Giá trị hiện tại', related='ma_ts.gia_tri_hien_tai', store=True, readonly=True)
    so_tien_khau_hao = fields.Float('Số tiền khấu hao', required=True, default=0)
    gia_tri_con_lai = fields.Float(string='Giá trị còn lại', store=True)

    @api.onchange('so_tien_khau_hao', 'ma_ts')
    def _onchange_so_tien_khau_hao(self):
        # Trong onchange, self là single record — không dùng vòng lặp for
        # Dùng _origin để truy cập bản ghi DB thực sự của trường Many2one
        ma_ts = self.ma_ts._origin if self.ma_ts else False
        if ma_ts and ma_ts.id:
            self.gia_tri_con_lai = max(0, ma_ts.gia_tri_hien_tai - self.so_tien_khau_hao)
        else:
            self.gia_tri_con_lai = 0
    
    loai_phieu = fields.Selection([
        ('automatic', 'Tự động'),
        ('manual', 'Thủ công')
    ], string='Phương thức', required=True)
    ghi_chu = fields.Char('Ghi chú')
    
    @api.model
    def create(self, vals):
        if self.env.context.get('install_mode'):
            return super().create(vals)

        if vals.get('ma_ts'):
            tai_san = self.env['tai_san'].browse(vals['ma_ts'])

            if tai_san.gia_tri_con_lai <= 0:
                raise ValidationError("Tài sản đã hết giá trị, không thể khấu hao !")

            if vals.get('so_tien_khau_hao', 0) > tai_san.gia_tri_con_lai:
                raise ValidationError("Số tiền khấu hao không được vượt quá giá trị còn lại!")

        return super().create(vals) 
