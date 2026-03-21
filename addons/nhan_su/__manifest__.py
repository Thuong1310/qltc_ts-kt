# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Nhân Sự",
    'summary': "Module quản lý nhân sự toàn diện: nhân viên, hợp đồng, chấm công, lương, KPI",
    'description': """
        Module Quản Lý Nhân Sự (QLNS) cung cấp đầy đủ các tính năng:
        - Quản lý nhân viên, phòng ban, chức vụ
        - Hợp đồng lao động (thử việc, chính thức, thời vụ)
        - Chấm công và quản lý nghỉ phép
        - Tính lương, phụ cấp và thưởng
        - Đánh giá năng lực KPI theo kỳ
    """,
    'author': "QLNS Team",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '2.0',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/qlns_demo.xml',
        'data/qlns_demo_full.xml',
        'views/nhan_vien.xml',
        'views/phong_ban.xml',
        'views/chuc_vu.xml',
        'views/lich_su_cong_tac.xml',
        'views/hop_dong_lao_dong.xml',
        'views/cham_cong.xml',
        'views/nghi_phep.xml',
        'views/luong.xml',
        'views/kpi.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
