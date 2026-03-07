# -*- coding: utf-8 -*-
"""
Dashboard Tổng Hợp TechCorp - ~450 dòng
Cung cấp toàn bộ dữ liệu KPI cho Dashboard Chart.js:
  - KPI Cards: Nhân Sự, Tài Chính, Tài Sản
  - Chart data: Cột, Tròn, Đường
  - Bảng nhanh: Top tài sản, nhân viên mới, bút toán chờ duyệt
"""
from odoo import models, fields, api
from datetime import date, timedelta
import json


class DashboardTongHop(models.Model):
    _name = 'upg.dashboard'
    _description = 'Dashboard Tổng Hợp TechCorp'
    _rec_name = 'ten'

    ten = fields.Char(default='Dashboard TechCorp', readonly=True)
    ngay_cap_nhat = fields.Datetime(string='Cập Nhật Lúc', readonly=True)

    # =============================================
    # KPI NHÂN SỰ
    # =============================================
    kpi_tong_nv        = fields.Integer('Tổng NV',         compute='_compute_kpi_ns', store=False)
    kpi_nv_dang_lam    = fields.Integer('NV Đang Làm',     compute='_compute_kpi_ns', store=False)
    kpi_nv_thu_viec    = fields.Integer('NV Thử Việc',     compute='_compute_kpi_ns', store=False)
    kpi_nv_nghi_viec   = fields.Integer('NV Nghỉ Việc',    compute='_compute_kpi_ns', store=False)
    kpi_luong_thang    = fields.Float('CP Lương Tháng',    compute='_compute_kpi_ns', store=False, digits=(18, 0))
    kpi_so_phong_ban   = fields.Integer('Số PB',           compute='_compute_kpi_ns', store=False)
    kpi_hop_dong_sap_het = fields.Integer('HĐ Sắp Hết Hạn', compute='_compute_kpi_ns', store=False)

    # =============================================
    # KPI TÀI CHÍNH
    # =============================================
    kpi_bt_cho_duyet    = fields.Integer('BT Chờ Duyệt',    compute='_compute_kpi_tc', store=False)
    kpi_bt_da_ghi_so    = fields.Integer('BT Đã Ghi Sổ',    compute='_compute_kpi_tc', store=False)
    kpi_cp_luong_thang  = fields.Float('CP Lương',           compute='_compute_kpi_tc', store=False, digits=(18, 0))
    kpi_cp_khau_hao_thang = fields.Float('CP KH Tháng',     compute='_compute_kpi_tc', store=False, digits=(18, 0))
    kpi_doanh_thu_thang = fields.Float('DT Tháng',          compute='_compute_kpi_tc', store=False, digits=(18, 0))
    kpi_mua_sam_cho_duyet = fields.Integer('Mua Sắm CD',    compute='_compute_kpi_tc', store=False)

    # =============================================
    # KPI TÀI SẢN
    # =============================================
    kpi_tong_tai_san      = fields.Integer('Tổng TSCĐ',       compute='_compute_kpi_ts', store=False)
    kpi_ts_dang_su_dung   = fields.Integer('TS Đang SD',      compute='_compute_kpi_ts', store=False)
    kpi_ts_cho_dua_vao    = fields.Integer('TS Chờ Đưa Vào',  compute='_compute_kpi_ts', store=False)
    kpi_ts_bao_tri        = fields.Integer('TS Bảo Trì',      compute='_compute_kpi_ts', store=False)
    kpi_tong_nguyen_gia   = fields.Float('Tổng NG',           compute='_compute_kpi_ts', store=False, digits=(18, 0))
    kpi_tong_gtcl         = fields.Float('Tổng GTCL',         compute='_compute_kpi_ts', store=False, digits=(18, 0))
    kpi_ty_le_khau_hao    = fields.Float('% Đã Khấu Hao',     compute='_compute_kpi_ts', store=False)
    kpi_kh_cho_ghi_so     = fields.Integer('KH Chờ Ghi Sổ',   compute='_compute_kpi_ts', store=False)

    # =============================================
    # CHART DATA (JSON strings)
    # =============================================
    chart_cp_thang        = fields.Text('Chart CP Tháng',     compute='_compute_charts', store=False)
    chart_nv_phong_ban    = fields.Text('Chart NV PB',        compute='_compute_charts', store=False)
    chart_ts_loai         = fields.Text('Chart TS Loại',      compute='_compute_charts', store=False)
    chart_luong_12thang   = fields.Text('Chart Lương 12T',    compute='_compute_charts', store=False)
    chart_bt_nguon        = fields.Text('Chart BT Nguồn',     compute='_compute_charts', store=False)

    # =============================================
    # BẢNG NHANH (JSON strings)
    # =============================================
    bang_top_tai_san      = fields.Text('Top 5 TS',           compute='_compute_bang_nhanh', store=False)
    bang_nv_moi           = fields.Text('NV Mới 30 Ngày',     compute='_compute_bang_nhanh', store=False)
    bang_bt_cho_duyet     = fields.Text('BT Chờ Duyệt',       compute='_compute_bang_nhanh', store=False)
    bang_mua_sam_cd       = fields.Text('Mua Sắm Chờ Duyệt',  compute='_compute_bang_nhanh', store=False)

    # =============================================
    # COMPUTE METHODS
    # =============================================

    @api.depends()
    def _compute_kpi_ns(self):
        for r in self:
            NV = self.env['ns.nhan_vien']
            r.kpi_tong_nv = NV.search_count([])
            r.kpi_nv_dang_lam = NV.search_count([('trang_thai', '=', 'dang_lam')])
            r.kpi_nv_thu_viec = NV.search_count([('trang_thai', '=', 'thu_viec')])
            r.kpi_nv_nghi_viec = NV.search_count([('trang_thai', '=', 'nghi_viec')])
            r.kpi_so_phong_ban = self.env['ns.phong_ban'].search_count([('active', '=', True)])
            # Hợp đồng sắp hết hạn trong 30 ngày
            ngay_30 = date.today() + timedelta(days=30)
            r.kpi_hop_dong_sap_het = self.env['ns.hop_dong'].search_count([
                ('ngay_ket_thuc', '<=', ngay_30),
                ('ngay_ket_thuc', '>=', date.today()),
                ('trang_thai', '=', 'da_ky'),
            ])
            # Lương tháng hiện tại
            today = date.today()
            bl = self.env['ns.bang_luong'].search([
                ('thang', '=', today.month), ('nam', '=', today.year),
                ('trang_thai', 'in', ['da_duyet', 'da_tra']),
            ])
            r.kpi_luong_thang = sum(bl.mapped('chi_phi_cong_ty'))

    @api.depends()
    def _compute_kpi_tc(self):
        for r in self:
            BT = self.env['qtc.but_toan']
            r.kpi_bt_cho_duyet = BT.search_count([('trang_thai', '=', 'cho_duyet')])
            r.kpi_bt_da_ghi_so = BT.search_count([('trang_thai', '=', 'da_ghi_so')])
            today = date.today()
            bts_thang = BT.search([
                ('thang', '=', today.month),
                ('nam', '=', today.year),
                ('trang_thai', 'in', ['da_duyet', 'da_ghi_so']),
            ])
            r.kpi_cp_luong_thang = sum(bts_thang.filtered(lambda b: b.loai == 'chi_phi_luong').mapped('so_tien'))
            r.kpi_cp_khau_hao_thang = sum(bts_thang.filtered(lambda b: b.loai == 'khau_hao').mapped('so_tien'))
            r.kpi_doanh_thu_thang = sum(bts_thang.filtered(lambda b: b.loai == 'doanh_thu').mapped('so_tien'))
            r.kpi_mua_sam_cho_duyet = self.env['qts.mua_sam'].search_count([
                ('trang_thai', 'in', ['cho_truong_phong', 'cho_ke_toan', 'cho_giam_doc'])
            ])

    @api.depends()
    def _compute_kpi_ts(self):
        for r in self:
            TS = self.env['qts.tai_san']
            all_ts = TS.search([])
            r.kpi_tong_tai_san = len(all_ts)
            r.kpi_ts_dang_su_dung = TS.search_count([('trang_thai', '=', 'dang_su_dung')])
            r.kpi_ts_cho_dua_vao = TS.search_count([('trang_thai', '=', 'cho_dua_vao_su_dung')])
            r.kpi_ts_bao_tri = TS.search_count([('trang_thai', '=', 'bao_tri')])
            r.kpi_tong_nguyen_gia = sum(all_ts.mapped('nguyen_gia'))
            r.kpi_tong_gtcl = sum(all_ts.mapped('gia_tri_con_lai'))
            tong_kh = sum(all_ts.mapped('tong_khau_hao_luy_ke'))
            r.kpi_ty_le_khau_hao = round(tong_kh / r.kpi_tong_nguyen_gia * 100, 1) if r.kpi_tong_nguyen_gia else 0
            r.kpi_kh_cho_ghi_so = self.env['qts.khau_hao'].search_count([('trang_thai', '=', 'cho_ghi_so')])

    @api.depends()
    def _compute_charts(self):
        for r in self:
            today = date.today()
            nam = today.year
            BT = self.env['qtc.but_toan']

            # 1. Chi phí theo tháng (12 tháng gần nhất)
            labels, luong, khau_hao, khac, doanh_thu = [], [], [], [], []
            for i in range(12):
                thang = (today.month - 11 + i - 1) % 12 + 1
                nam_i = nam - 1 if (today.month - 11 + i - 1) < 0 else nam
                bts = BT.search([('thang', '=', thang), ('nam', '=', nam_i),
                                  ('trang_thai', 'in', ['da_duyet', 'da_ghi_so'])])
                labels.append(f'T{thang}/{str(nam_i)[2:]}')
                luong.append(sum(bts.filtered(lambda b: b.loai == 'chi_phi_luong').mapped('so_tien')))
                khau_hao.append(sum(bts.filtered(lambda b: b.loai == 'khau_hao').mapped('so_tien')))
                khac.append(sum(bts.filtered(lambda b: b.loai not in ('chi_phi_luong', 'khau_hao', 'doanh_thu')).mapped('so_tien')))
                doanh_thu.append(sum(bts.filtered(lambda b: b.loai == 'doanh_thu').mapped('so_tien')))
            r.chart_cp_thang = json.dumps({
                'labels': labels,
                'datasets': [
                    {'label': 'Chi Phí Lương', 'data': luong, 'backgroundColor': 'rgba(255,99,132,0.7)', 'borderColor': '#ff6384', 'type': 'bar'},
                    {'label': 'Khấu Hao', 'data': khau_hao, 'backgroundColor': 'rgba(255,159,64,0.7)', 'borderColor': '#ff9f40', 'type': 'bar'},
                    {'label': 'CP Khác', 'data': khac, 'backgroundColor': 'rgba(201,203,207,0.7)', 'borderColor': '#c9cbcf', 'type': 'bar'},
                    {'label': 'Doanh Thu', 'data': doanh_thu, 'borderColor': '#36a2eb', 'backgroundColor': 'transparent', 'type': 'line', 'tension': 0.4},
                ],
            })

            # 2. Nhân viên theo phòng ban (pie)
            pb_list = self.env['ns.phong_ban'].search([('active', '=', True)])
            r.chart_nv_phong_ban = json.dumps({
                'labels': [pb.ten_phong_ban for pb in pb_list],
                'datasets': [{
                    'data': [self.env['ns.nhan_vien'].search_count([
                        ('phong_ban_id', '=', pb.id), ('trang_thai', '=', 'dang_lam')
                    ]) for pb in pb_list],
                    'backgroundColor': [
                        '#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF',
                        '#FF9F40','#FF6384','#C9CBCF','#7FC97F','#BEAED4',
                    ],
                }],
            })

            # 3. Tài sản theo loại (doughnut)
            loai_list = self.env['qts.loai_tai_san'].search([])
            ts_loai_data, ts_loai_labels = [], []
            for loai in loai_list:
                count = self.env['qts.tai_san'].search_count([
                    ('loai_tai_san_id', '=', loai.id),
                    ('trang_thai', '!=', 'thanh_ly'),
                ])
                if count > 0:
                    ts_loai_labels.append(loai.ten_loai)
                    ts_loai_data.append(count)
            r.chart_ts_loai = json.dumps({
                'labels': ts_loai_labels,
                'datasets': [{
                    'data': ts_loai_data,
                    'backgroundColor': ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40'],
                }],
            })

            # 4. Lương 12 tháng (line chart)
            luong_12, labels_12 = [], []
            for i in range(12):
                thang = (today.month - 11 + i - 1) % 12 + 1
                nam_i = nam - 1 if (today.month - 11 + i - 1) < 0 else nam
                bl = self.env['ns.bang_luong'].search([
                    ('thang', '=', thang), ('nam', '=', nam_i),
                    ('trang_thai', 'in', ['da_duyet', 'da_tra']),
                ])
                labels_12.append(f'T{thang}/{str(nam_i)[2:]}')
                luong_12.append(sum(bl.mapped('chi_phi_cong_ty')))
            r.chart_luong_12thang = json.dumps({
                'labels': labels_12,
                'datasets': [{
                    'label': 'Chi Phí Lương (VNĐ)',
                    'data': luong_12,
                    'borderColor': '#FF6384',
                    'backgroundColor': 'rgba(255,99,132,0.1)',
                    'tension': 0.4,
                    'fill': True,
                }],
            })

            # 5. Bút toán: tự động vs thủ công (pie)
            tu_dong = BT.search_count([('nguon_tao', '!=', 'thu_cong')])
            thu_cong_bt = BT.search_count([('nguon_tao', '=', 'thu_cong')])
            r.chart_bt_nguon = json.dumps({
                'labels': ['🤖 Tự Động', '✍️ Thủ Công'],
                'datasets': [{'data': [tu_dong, thu_cong_bt], 'backgroundColor': ['#4BC0C0', '#FF9F40']}],
            })

    @api.depends()
    def _compute_bang_nhanh(self):
        for r in self:
            # Top 5 tài sản theo nguyên giá
            top_ts = self.env['qts.tai_san'].search(
                [('trang_thai', '!=', 'thanh_ly')], order='nguyen_gia desc', limit=5
            )
            r.bang_top_tai_san = json.dumps([{
                'ma': ts.ma_tai_san,
                'ten': ts.ten_tai_san,
                'loai': ts.loai_tai_san_id.ten_loai if ts.loai_tai_san_id else '',
                'nguyen_gia': ts.nguyen_gia,
                'gtcl': ts.gia_tri_con_lai,
                'trang_thai': ts.trang_thai,
            } for ts in top_ts])

            # NV mới trong 30 ngày
            ngay_30 = date.today() - timedelta(days=30)
            nv_moi = self.env['ns.nhan_vien'].search([('ngay_vao_lam', '>=', ngay_30)], order='ngay_vao_lam desc', limit=5)
            r.bang_nv_moi = json.dumps([{
                'ma': nv.ma_nhan_vien,
                'ho_ten': nv.ho_ten,
                'phong_ban': nv.phong_ban_id.ten_phong_ban if nv.phong_ban_id else '',
                'chuc_danh': nv.chuc_danh_id.ten_chuc_danh if nv.chuc_danh_id else '',
                'ngay_vao_lam': str(nv.ngay_vao_lam) if nv.ngay_vao_lam else '',
            } for nv in nv_moi])

            # Bút toán chờ duyệt (mới nhất)
            bts = self.env['qtc.but_toan'].search([('trang_thai', '=', 'cho_duyet')], order='id desc', limit=5)
            r.bang_bt_cho_duyet = json.dumps([{
                'ma': bt.ma_but_toan,
                'ten': bt.ten_but_toan,
                'loai': bt.loai,
                'so_tien': bt.so_tien,
                'nguon_tao': bt.nguon_tao,
            } for bt in bts])

            # Mua sắm chờ duyệt
            mss = self.env['qts.mua_sam'].search([
                ('trang_thai', 'in', ['cho_truong_phong', 'cho_ke_toan', 'cho_giam_doc'])
            ], order='id desc', limit=5)
            r.bang_mua_sam_cd = json.dumps([{
                'so': ms.so_de_nghi,
                'ten': ms.ten_tai_san,
                'phong_ban': ms.phong_ban_id.ten_phong_ban if ms.phong_ban_id else '',
                'tong_gia_tri': ms.tong_gia_tri,
                'trang_thai': ms.trang_thai,
            } for ms in mss])

    # =============================================
    # PUBLIC API METHODS (for JS RPC)
    # =============================================

    @api.model
    def get_all_kpi(self):
        """Trả về toàn bộ KPI cho Dashboard JS"""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({'ten': 'Dashboard TechCorp'})
        return {
            'nhan_su': {
                'tong_nv': rec.kpi_tong_nv,
                'dang_lam': rec.kpi_nv_dang_lam,
                'thu_viec': rec.kpi_nv_thu_viec,
                'nghi_viec': rec.kpi_nv_nghi_viec,
                'luong_thang': rec.kpi_luong_thang,
                'so_phong_ban': rec.kpi_so_phong_ban,
                'hop_dong_sap_het': rec.kpi_hop_dong_sap_het,
            },
            'tai_chinh': {
                'bt_cho_duyet': rec.kpi_bt_cho_duyet,
                'bt_da_ghi_so': rec.kpi_bt_da_ghi_so,
                'cp_luong': rec.kpi_cp_luong_thang,
                'cp_khau_hao': rec.kpi_cp_khau_hao_thang,
                'doanh_thu': rec.kpi_doanh_thu_thang,
                'mua_sam_cho_duyet': rec.kpi_mua_sam_cho_duyet,
            },
            'tai_san': {
                'tong': rec.kpi_tong_tai_san,
                'dang_su_dung': rec.kpi_ts_dang_su_dung,
                'cho_dua_vao': rec.kpi_ts_cho_dua_vao,
                'bao_tri': rec.kpi_ts_bao_tri,
                'tong_nguyen_gia': rec.kpi_tong_nguyen_gia,
                'tong_gtcl': rec.kpi_tong_gtcl,
                'ty_le_khau_hao': rec.kpi_ty_le_khau_hao,
                'kh_cho_ghi_so': rec.kpi_kh_cho_ghi_so,
            },
            'charts': {
                'cp_thang': rec.chart_cp_thang,
                'nv_phong_ban': rec.chart_nv_phong_ban,
                'ts_loai': rec.chart_ts_loai,
                'luong_12thang': rec.chart_luong_12thang,
                'bt_nguon': rec.chart_bt_nguon,
            },
            'bang_nhanh': {
                'top_tai_san': rec.bang_top_tai_san,
                'nv_moi': rec.bang_nv_moi,
                'bt_cho_duyet': rec.bang_bt_cho_duyet,
                'mua_sam_cd': rec.bang_mua_sam_cd,
            },
        }
