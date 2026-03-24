# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

_logger = logging.getLogger(__name__)

class DeXuatMuaTaiSan(models.Model):
    _name = 'de_xuat_mua_tai_san'
    _description = 'Đề xuất mua tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_de_xuat'
    _order = 'ngay_de_xuat desc'

    ma_de_xuat = fields.Char(
        string='Mã đề xuất', required=True,
        copy=False, default='New', tracking=True,
    )
    ten_de_xuat = fields.Char(string='Tiêu đề đề xuất', required=True, tracking=True)
    ngay_de_xuat = fields.Date(string='Ngày đề xuất', default=fields.Date.context_today, required=True, tracking=True)
    nguoi_de_xuat_id = fields.Many2one(
        'nhan_vien',
        string='Người đề xuất',
        default=lambda self: self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1),
        ondelete='set null',
        tracking=True
    )
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban', ondelete='set null', tracking=True)
    line_ids = fields.One2many('de_xuat_mua_tai_san.line', 'de_xuat_id', string='Chi tiết thiết bị')
    tong_gia_tri = fields.Float(string='Tổng giá trị', compute='_compute_tong_gia_tri', store=True, tracking=True)
    don_vi_tien_te = fields.Selection([('vnd', 'VNĐ'), ('usd', 'USD')], string='Đơn vị tiền tệ', default='vnd', required=True)
    ly_do = fields.Text(string='Lý do đề xuất', required=True, tracking=True)
    mo_ta = fields.Html(string='Mô tả chi tiết', tracking=True)
    dinh_kem_ids = fields.Many2many('ir.attachment', string='File đính kèm')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('waiting_approval', 'Chờ phê duyệt tài chính'),
        ('approved', 'Đã phê duyệt'),
        ('rejected', 'Từ chối'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='draft', required=True, tracking=True)
    ngay_du_kien_nhan = fields.Date(string='Ngày dự kiến nhận hàng', tracking=True)
    phe_duyet_id = fields.Many2one('phe_duyet_mua_tai_san', string='Đơn phê duyệt', readonly=True, ondelete='set null', tracking=True)
    tai_san_ids = fields.Many2many('tai_san', string='Tài sản đã tạo', readonly=True)
    tai_san_count = fields.Integer(string='Số lượng tài sản', compute='_compute_tai_san_count')
    ghi_chu = fields.Text(string='Ghi chú', tracking=True)

    @api.depends('tai_san_ids')
    def _compute_tai_san_count(self):
        for record in self:
            record.tai_san_count = len(record.tai_san_ids)

    @api.depends('line_ids.thanh_tien')
    def _compute_tong_gia_tri(self):
        for record in self:
            record.tong_gia_tri = sum(record.line_ids.mapped('thanh_tien'))

    @api.model
    def default_get(self, fields_list):
        """
        Override default_get để đảm bảo các trường Many2one cross-module
        không tạo ra _unknown object khi onchange chạy trên record mới.
        """
        res = super().default_get(fields_list)
        # Các trường Many2one tham chiếu module khác có thể gây _unknown
        cross_module_fields = ['phe_duyet_id', 'phong_ban_id']
        for fname in cross_module_fields:
            if fname in res and not res[fname]:
                res[fname] = False
            elif fname not in res:
                res[fname] = False
        return res

    def _sanitize_many2one_fields(self):
        """
        Sanitize tất cả trường Many2one trên record này để tránh _unknown object.
        Được gọi trước khi Odoo tính snapshot diff trong onchange.
        """
        many2one_fields = [
            fname for fname, field in self._fields.items()
            if field.type == 'many2one'
        ]
        for fname in many2one_fields:
            try:
                val = self[fname]
                if not val:
                    continue
                try:
                    rec_id = val.id
                    # _unknown object: id là NewId hoặc không phải int dương
                    if rec_id and not isinstance(rec_id, int):
                        self[fname] = False
                except AttributeError:
                    self[fname] = False
            except Exception:
                pass

    @api.onchange('nguoi_de_xuat_id', 'phong_ban_id', 'phe_duyet_id')
    def _onchange_sanitize_many2one(self):
        """Sanitize Many2one fields khi onchange để tránh _unknown crash"""
        self._sanitize_many2one_fields()

    def onchange(self, values, field_name, field_onchange):
        """
        Override Odoo onchange để bắt lỗi _unknown object trong snapshot diff.
        Xóa các Many2one field có giá trị invalid trước khi tính diff.
        """
        # Sanitize values dict trước khi truyền vào Odoo
        many2one_fields = [
            fname for fname, field in self._fields.items()
            if field.type == 'many2one'
        ]
        for fname in many2one_fields:
            if fname in values:
                val = values[fname]
                # Giá trị Many2one từ client là [id, name] hoặc False/None
                if isinstance(val, (list, tuple)) and len(val) >= 1:
                    try:
                        int(val[0])  # Kiểm tra id có phải số hợp lệ không
                    except (TypeError, ValueError):
                        values[fname] = False
                elif val and not isinstance(val, int):
                    values[fname] = False
        try:
            return super().onchange(values, field_name, field_onchange)
        except AttributeError as e:
            if '_unknown' in str(e) or 'has no attribute' in str(e):
                import logging
                logging.getLogger(__name__).warning(
                    'de_xuat_mua_tai_san onchange: caught _unknown object error, '
                    'returning empty result. Error: %s', e
                )
                return {}
            raise

    @api.model
    def create(self, vals):
        if vals.get('ma_de_xuat', 'New') == 'New':
            vals['ma_de_xuat'] = self.env['ir.sequence'].next_by_code('de_xuat_mua_tai_san') or 'New'
        # Đảm bảo các trường Many2one cross-module không có giá trị invalid
        for fname in ['phe_duyet_id', 'phong_ban_id']:
            if fname in vals and not vals[fname]:
                vals[fname] = False
        return super().create(vals)

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('Vui lòng thêm ít nhất một thiết bị vào đề xuất.'))
            for line in record.line_ids:
                if not line.danh_muc_ts_id:
                    raise UserError(_('Vui lòng chọn danh mục tài sản cho thiết bị: %s') % (line.ten_thiet_bi or '(Chưa đặt tên)'))
            if record.tong_gia_tri <= 0:
                raise UserError(_('Tổng giá trị phải lớn hơn 0.'))
            record.state = 'submitted'
            record._create_approval_request()
            record.state = 'waiting_approval'
            record.message_post(body=_('Đề xuất đã được gửi và tạo đơn phê duyệt tài chính.'))

    def _create_approval_request(self):
        self.ensure_one()
        if not self.env['ir.module.module'].search([('name', '=', 'quan_ly_tai_chinh'), ('state', '=', 'installed')]):
            raise UserError(_('Module Quản lý tài chính chưa được cài đặt.'))

        line_vals = []
        for line in self.line_ids:
            danh_muc_id = line.danh_muc_ts_id.id if line.danh_muc_ts_id and line.danh_muc_ts_id.exists() else False
            if not danh_muc_id:
                raise UserError(_('Thiết bị "%s" chưa có danh mục tài sản hợp lệ.') % (line.ten_thiet_bi or '(Chưa đặt tên)'))
            line_vals.append((0, 0, {
                'ten_thiet_bi': line.ten_thiet_bi or '',
                'danh_muc_ts_id': danh_muc_id,
                'mo_ta': line.mo_ta or '',
                'thong_so_ky_thuat': line.thong_so_ky_thuat or '',
                'so_luong': line.so_luong or 1,
                'don_vi_tinh': line.don_vi_tinh or '',
                'don_gia': line.don_gia or 0.0,
                'thanh_tien': line.thanh_tien or 0.0,
                'pp_khau_hao': line.pp_khau_hao or 'straight-line',
                'thoi_gian_su_dung': line.thoi_gian_su_dung or 0,
                'ty_le_khau_hao': line.ty_le_khau_hao or 0.0,
                'nha_cung_cap': line.nha_cung_cap or '',
            }))

        phe_duyet_vals = {
            'de_xuat_mua_id': self.id,
            'ten_de_xuat': self.ten_de_xuat or '',
            'ngay_de_xuat': self.ngay_de_xuat or fields.Date.today(),
            'nguoi_de_xuat_id': self.nguoi_de_xuat_id.id if self.nguoi_de_xuat_id else False,
            'phong_ban_id': self.phong_ban_id.id if self.phong_ban_id else False,
            'tong_gia_tri': self.tong_gia_tri or 0.0,
            'don_vi_tien_te': self.don_vi_tien_te or 'vnd',
            'ly_do': self.ly_do or '',
            'mo_ta': self.mo_ta or '',
            'ngay_du_kien_nhan': self.ngay_du_kien_nhan or False,
            'line_ids': line_vals,
        }
        phe_duyet = self.env['phe_duyet_mua_tai_san'].create(phe_duyet_vals)
        self.phe_duyet_id = phe_duyet.id

        try:
            finance_users = self.env.ref('quan_ly_tai_chinh.group_finance_manager').users
            if finance_users:
                phe_duyet.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=finance_users[0].id,
                    summary=f'Phê duyệt đề xuất mua tài sản: {self.ma_de_xuat}'
                )
        except Exception:
            pass
        return phe_duyet

    def action_cancel(self):
        for record in self:
            if record.state == 'approved':
                raise UserError(_('Không thể hủy đề xuất đã được phê duyệt.'))
            if record.phe_duyet_id and record.phe_duyet_id.state == 'draft':
                record.phe_duyet_id.action_cancel()
            record.state = 'cancelled'

    def action_reset_to_draft(self):
        for record in self:
            if record.state in ('approved', 'rejected', 'done', 'cancelled'):
                record.with_context(from_finance_approval=True).write({
                    'state': 'draft',
                    'phe_duyet_id': False,
                })
                record.message_post(body=_('Trạng thái đã được reset về nháp.'))
        return True

    def action_view_approval(self):
        self.ensure_one()
        if not self.phe_duyet_id:
            raise UserError(_('Chưa có đơn phê duyệt nào được tạo.'))
        return {
            'name': _('Đơn phê duyệt mua tài sản'),
            'type': 'ir.actions.act_window',
            'res_model': 'phe_duyet_mua_tai_san',
            'view_mode': 'form',
            'res_id': self.phe_duyet_id.id,
            'target': 'current',
        }

    def action_view_assets(self):
        self.ensure_one()
        return {
            'name': _('Tài sản đã tạo'),
            'type': 'ir.actions.act_window',
            'res_model': 'tai_san',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.tai_san_ids.ids)],
            'context': {'create': False}
        }

    def write(self, vals):
        if 'state' in vals and vals['state'] in ['approved', 'rejected']:
            # Cho phép bypass khi load demo/data (install_mode) hoặc gọi từ module tài chính
            bypass = (
                self.env.context.get('from_finance_approval')
                or self.env.context.get('install_mode')
            )
            if not bypass:
                raise UserError(_(
                    'Đề xuất mua tài sản chỉ có thể được phê duyệt thông qua '
                    'module Quản lý Tài chính.\n\n'
                    'Vui lòng vào: Tài chính > Phê duyệt mua tài sản.'
                ))
        return super().write(vals)

    def _on_approval_approved(self):
        self.ensure_one()
        self.with_context(from_finance_approval=True).write({'state': 'approved'})
        self.message_post(body=_('Đề xuất đã được phê duyệt bởi bộ phận tài chính.'))

    def _on_approval_rejected(self):
        self.ensure_one()
        self.with_context(from_finance_approval=True).write({'state': 'rejected'})
        self.message_post(body=_('Đề xuất đã bị từ chối bởi bộ phận tài chính.'))

    def _on_approval_deleted(self):
        self.ensure_one()
        try:
            self.with_context(from_finance_approval=True).write({'state': 'draft', 'phe_duyet_id': False})
            self.message_post(body=_('Đơn phê duyệt đã bị xóa. Đề xuất trở về trạng thái nháp.'))
        except Exception as e:
            _logger.warning(f"Could not reset de_xuat_mua_tai_san {self.id}: {e}")


class DeXuatMuaTaiSanLine(models.Model):
    _name = 'de_xuat_mua_tai_san.line'
    _description = 'Chi tiết đề xuất mua tài sản'
    _order = 'sequence, id'

    sequence = fields.Integer(string='STT', default=10)
    de_xuat_id = fields.Many2one('de_xuat_mua_tai_san', string='Đề xuất', required=True, ondelete='cascade', index=True)
    ten_thiet_bi = fields.Char(string='Tên thiết bị', required=True)
    danh_muc_ts_id = fields.Many2one('danh_muc_tai_san', string='Danh mục tài sản', ondelete='set null')
    mo_ta = fields.Text(string='Mô tả')
    thong_so_ky_thuat = fields.Text(string='Thông số kỹ thuật')
    so_luong = fields.Integer(string='Số lượng', default=1, required=True)
    don_vi_tinh = fields.Char(string='Đơn vị tính', default='Chiếc', required=True)
    don_gia = fields.Float(string='Đơn giá', required=True)
    thanh_tien = fields.Float(string='Thành tiền', compute='_compute_thanh_tien', store=True)
    pp_khau_hao = fields.Selection([
        ('straight-line', 'Khấu hao tuyến tính'),
        ('degressive', 'Khấu hao giảm dần'),
        ('none', 'Không khấu hao')
    ], string='Phương pháp khấu hao', default='straight-line', required=True)
    thoi_gian_su_dung = fields.Integer(string='Thời gian sử dụng (năm)', default=5)
    ty_le_khau_hao = fields.Float(string='Tỷ lệ khấu hao (%/năm)', compute='_compute_ty_le_khau_hao', store=True, readonly=False)
    nha_cung_cap = fields.Char(string='Nhà cung cấp đề xuất')

    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.don_gia

    @api.depends('thoi_gian_su_dung')
    def _compute_ty_le_khau_hao(self):
        for record in self:
            if record.thoi_gian_su_dung and record.thoi_gian_su_dung > 0:
                record.ty_le_khau_hao = 100.0 / record.thoi_gian_su_dung
            else:
                record.ty_le_khau_hao = 0.0

    @api.onchange('danh_muc_ts_id')
    def _onchange_danh_muc_ts_id(self):
        """Xử lý an toàn _unknown object trong onchange"""
        try:
            if not self.danh_muc_ts_id:
                return
            try:
                _ = self.danh_muc_ts_id.id
            except AttributeError:
                self.danh_muc_ts_id = False
        except Exception:
            pass

    @api.constrains('so_luong', 'don_gia', 'thoi_gian_su_dung', 'ty_le_khau_hao')
    def _check_positive_values(self):
        for record in self:
            if record.so_luong <= 0:
                raise ValidationError(_('Số lượng phải lớn hơn 0.'))
            if record.don_gia < 0:
                raise ValidationError(_('Đơn giá không thể âm.'))
            if record.pp_khau_hao != 'none':
                if record.thoi_gian_su_dung <= 0:
                    raise ValidationError(_('Thời gian sử dụng phải lớn hơn 0 nếu có khấu hao.'))
                if record.ty_le_khau_hao <= 0 or record.ty_le_khau_hao > 100:
                    raise ValidationError(_('Tỷ lệ khấu hao phải trong khoảng 0-100%.'))