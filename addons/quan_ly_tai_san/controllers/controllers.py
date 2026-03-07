# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TaiSanController(http.Controller):

    @http.route('/tai_san/api/thong_ke', type='json', auth='user')
    def get_thong_ke(self, **kwargs):
        TS = request.env['qts.tai_san']
        return {
            'tong_tai_san': TS.search_count([]),
            'dang_su_dung': TS.search_count([('trang_thai', '=', 'dang_su_dung')]),
            'cho_dua_vao': TS.search_count([('trang_thai', '=', 'cho_dua_vao_su_dung')]),
            'tong_nguyen_gia': sum(TS.search([]).mapped('nguyen_gia')),
            'tong_gtcl': sum(TS.search([]).mapped('gia_tri_con_lai')),
        }
