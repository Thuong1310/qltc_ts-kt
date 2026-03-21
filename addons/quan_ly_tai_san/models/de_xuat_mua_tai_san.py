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
        string='Mã đề xuất',
        required=False,
        copy=False,
        readonly=True,
        # KHÔNG dùng default lambda sequence ở đây vì gây conflict với create()
        # Giá trị sẽ được gán trong create() và default_get()
        tracking=True,
    )
    ten_de_xuat = fields.Char(string='Tiêu đề đề xuất', required=True, tracking=True)
    ngay_de_xuat = fields.Date(string='Ngày đề xuất', default=fields.Date.context_today, required=True, tracking=True)

    # QUAN TRỌNG: Bỏ tracking=True cho các Many2one cross-module
    # vì mail tracking sẽ cố gọi .id trên _unknown object → crash
    nguoi_de_xuat_id = fields.Many2one(
        'nhan_vien',
        string='Người đề xuất',
        ondelete='set null',
        tracking=False,  # Tắt tracking để tránh lỗi _unknown trong mail.tracking.value
    )
    phong_ban_id = fields.Many2one(
        'phong_ban',
        string='Phòng ban',
        ondelete='set null',
        tracking=False,  # Tắt tracking
    )
    line_ids = fields.One2many('de_xuat_mua_tai_san.line', 'de_xuat_id', string='Chi tiết thiết bị')
    tong_gia_tri = fields.Float(string='Tổng giá trị', compute='_compute_tong_gia_tri', store=True, tracking=True)
    don_vi_tien_te = fields.Selection([('vnd', 'VNĐ'), ('usd', 'USD')], string='Đơn vị tiền tệ', default='vnd', required=True)
    ly_do = fields.Text(string='Lý do đề xuất', required=True, tracking=True)
    mo_ta = fields.Html(string='Mô tả chi tiết', tracking=False)
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
    phe_duyet_id = fields.Many2one(
        'phe_duyet_mua_tai_san',
        string='Đơn phê duyệt',
        readonly=True,
        ondelete='set null',
        tracking=False,  # Tắt tracking
    )
    tai_san_ids = fields.Many2many('tai_san', string='Tài sản đã tạo', readonly=True)
    tai_san_count = fields.Integer(string='Số lượng tài sản', compute='_compute_tai_san_count')
    ghi_chu = fields.Text(string='Ghi chú', tracking=True)

    # ============ COMPUTE METHODS ============

    @api.depends('tai_san_ids')
    def _compute_tai_san_count(self):
        for record in self:
            record.tai_san_count = len(record.tai_san_ids)

    @api.depends('line_ids.thanh_tien')
    def _compute_tong_gia_tri(self):
        for record in self:
            record.tong_gia_tri = sum(record.line_ids.mapped('thanh_tien'))

    # ============ FIX _unknown: override _read_format ============

    def _get_m2o_field_names(self):
        return [fname for fname, f in self._fields.items() if f.type == 'many2one']

    def _fix_unknown_in_cache(self):
        """Xóa các entry _unknown khỏi env.cache để buộc đọc lại từ DB."""
        cache = self.env.cache
        for record in self:
            for fname in self._get_m2o_field_names():
                field_obj = self._fields[fname]
                try:
                    val = cache.get(record, field_obj)
                    try:
                        _ = val.id
                    except AttributeError:
                        cache.remove(record, field_obj)
                        _logger.warning('Fixed _unknown cache: %s.%s record=%s', self._name, fname, record.id)
                except Exception:
                    pass

    def _read_format(self, fnames, load='_classic_read'):
        """Override để bắt _unknown trong _read_format, xóa cache rồi đọc lại."""
        try:
            return super()._read_format(fnames=fnames, load=load)
        except AttributeError as e:
            if '_unknown' not in str(e) and "has no attribute 'id'" not in str(e):
                raise
            _logger.warning('de_xuat_mua_tai_san._read_format: fixing _unknown. Error: %s', e)
            self._fix_unknown_in_cache()
            try:
                return super()._read_format(fnames=fnames, load=load)
            except AttributeError as e2:
                _logger.error('de_xuat_mua_tai_san._read_format: still failing: %s', e2)
                m2o_names = set(self._get_m2o_field_names())
                safe_fnames = [f for f in fnames if f not in m2o_names]
                result = super()._read_format(fnames=safe_fnames, load=load)
                for row in result:
                    for fname in m2o_names:
                        if fname in fnames and fname not in row:
                            row[fname] = False
                return result

    # ============ DEFAULT_GET ============

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Gán mã đề xuất ngay khi mở form mới
        if 'ma_de_xuat' in fields_list and not res.get('ma_de_xuat'):
            res['ma_de_xuat'] = self.env['ir.sequence'].next_by_code('de_xuat_mua_tai_san') or 'New'
        # Gán người đề xuất an toàn (không dùng lambda để tránh _unknown)
        if 'nguoi_de_xuat_id' in fields_list and not res.get('nguoi_de_xuat_id'):
            try:
                nv = self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1)
                if nv and isinstance(nv.id, int) and nv.id > 0:
                    res['nguoi_de_xuat_id'] = nv.id
            except Exception:
                pass
        # Đảm bảo các Many2one cross-module không có giá trị invalid
        for fname in ['phe_duyet_id', 'phong_ban_id', 'nguoi_de_xuat_id']:
            if fname in res and not res[fname]:
                res[fname] = False
        return res

    # ============ SANITIZE HELPERS ============

    def _sanitize_many2one_fields(self):
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
                    if rec_id and not isinstance(rec_id, int):
                        self[fname] = False
                except AttributeError:
                    self[fname] = False
            except Exception:
                pass

    def _sanitize_vals_many2one(self, vals):
        """Sanitize dict vals: đảm bảo các Many2one không có giá trị _unknown."""
        for fname in self._get_m2o_field_names():
            if fname not in vals:
                continue
            v = vals[fname]
            if not v:
                vals[fname] = False
            elif isinstance(v, int) and v > 0:
                pass  # hợp lệ
            elif isinstance(v, (list, tuple)):
                pass  # command tuple
            else:
                vals[fname] = False
        return vals

    # ============ ONCHANGE ============

    @api.onchange('nguoi_de_xuat_id', 'phong_ban_id', 'phe_duyet_id')
    def _onchange_sanitize_many2one(self):
        self._sanitize_many2one_fields()

    def onchange(self, values, field_name, field_onchange):
        many2one_fields = [
            fname for fname, field in self._fields.items()
            if field.type == 'many2one'
        ]
        for fname in many2one_fields:
            if fname in values:
                val = values[fname]
                if isinstance(val, (list, tuple)) and len(val) >= 1:
                    try:
                        int(val[0])
                    except (TypeError, ValueError):
                        values[fname] = False
                elif val and not isinstance(val, int):
                    values[fname] = False
        try:
            return super().onchange(values, field_name, field_onchange)
        except AttributeError as e:
            if '_unknown' in str(e) or 'has no attribute' in str(e):
                _logger.warning('de_xuat_mua_tai_san onchange: _unknown caught. Error: %s', e)
                return {}
            raise

    # ============ CRUD ============

    @api.model
    def create(self, vals):
        # Tạo mã nếu chưa có
        if not vals.get('ma_de_xuat') or vals.get('ma_de_xuat') == 'New':
            vals['ma_de_xuat'] = self.env['ir.sequence'].next_by_code('de_xuat_mua_tai_san') or 'New'
        # Sanitize tất cả Many2one trong vals
        vals = self._sanitize_vals_many2one(vals)
        return super().create(vals)

    def write(self, vals):
        # Sanitize Many2one trong vals trước khi write (tránh _unknown vào tracking)
        vals = self._sanitize_vals_many2one(dict(vals))
        if 'state' in vals and vals['state'] in ['approved', 'rejected']:
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

    # ============ ACTION METHODS ============

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('Vui lòng thêm ít nhất một thiết bị vào đề xuất.'))
            for line in record.line_ids:
                if not line.danh_muc_ts_id:
                    raise UserError(_('Vui lòng chọn danh mục tài sản cho thiết bị: %s') % (line.ten_thiet_bi or '(Chưa đặt tên)'))
            if record.tong_gia_tri <= 0:
                raise UserError(_('Tổng giá trị phải lớn hơn 0.'))
            # Sanitize record trước khi write state (tránh mail tracking bị _unknown)
            record._sanitize_many2one_fields()
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

        # Lấy ID an toàn cho các Many2one
        nguoi_id = False
        try:
            if self.nguoi_de_xuat_id and isinstance(self.nguoi_de_xuat_id.id, int):
                nguoi_id = self.nguoi_de_xuat_id.id
        except AttributeError:
            pass

        phong_ban_id = False
        try:
            if self.phong_ban_id and isinstance(self.phong_ban_id.id, int):
                phong_ban_id = self.phong_ban_id.id
        except AttributeError:
            pass

        phe_duyet_vals = {
            'de_xuat_mua_id': self.id,
            'ten_de_xuat': self.ten_de_xuat or '',
            'ngay_de_xuat': self.ngay_de_xuat or fields.Date.today(),
            'nguoi_de_xuat_id': nguoi_id,
            'phong_ban_id': phong_ban_id,
            'tong_gia_tri': self.tong_gia_tri or 0.0,
            'don_vi_tien_te': self.don_vi_tien_te or 'vnd',
            'ly_do': self.ly_do or '',
            'mo_ta': self.mo_ta or '',
            'ngay_du_kien_nhan': self.ngay_du_kien_nhan or False,
            'line_ids': line_vals,
        }
        phe_duyet = self.env['phe_duyet_mua_tai_san'].create(phe_duyet_vals)
        # Gán phe_duyet_id trực tiếp qua SQL để tránh write() trigger tracking
        self.env.cr.execute(
            "UPDATE de_xuat_mua_tai_san SET phe_duyet_id = %s WHERE id = %s",
            (phe_duyet.id, self.id)
        )
        self.invalidate_cache(['phe_duyet_id'], [self.id])

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
            if record.phe_duyet_id and isinstance(record.phe_duyet_id.id, int) and record.phe_duyet_id.state == 'draft':
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

    # ============ FINANCE MODULE CALLBACKS ============

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