# -*- coding: utf-8 -*-
{
    'name': 'TechCorp Dashboard Tổng Hợp',
    'version': '15.0.2.0.0',
    'category': 'Dashboard',
    'summary': 'Dashboard tổng hợp KPI: Nhân Sự + Tài Chính + Tài Sản với biểu đồ Chart.js real-time',
    'description': '''
        Dashboard tổng hợp cho Ban Lãnh Đạo TechCorp:
        - KPI Cards: NV đang làm, CP lương tháng, GTCL tài sản, bút toán chờ duyệt
        - Biểu đồ cột: Chi phí theo tháng (lương / KH / khác)
        - Biểu đồ tròn: Nhân viên theo phòng ban
        - Biểu đồ tròn: Tài sản theo loại
        - Biểu đồ đường: Xu hướng chi phí 12 tháng
        - Bảng thống kê nhanh: Top tài sản, nhân viên mới, BT chờ duyệt
        - Auto-refresh mỗi 60 giây
        - Tích hợp Chart.js từ CDN
    ''',
    'author': 'TechCorp Internal',
    'depends': ['base', 'web', 'nhan_su', 'quan_ly_tai_chinh', 'quan_ly_tai_san'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_tong_hop_views.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/dashboard_tong_hop.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'application': True,
}
