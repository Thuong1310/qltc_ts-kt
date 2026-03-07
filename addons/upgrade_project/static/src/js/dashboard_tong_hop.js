/**
 * Dashboard Tổng Hợp TechCorp - Odoo 15 OWL 1 Syntax
 * ~550 dòng
 */
odoo.define('upgrade_project.dashboard_tong_hop', function (require) {
    'use strict';

    const { Component, useState, onMounted, onWillUnmount, useRef } = owl;
    const { registry } = require('@web/core/registry');
    const { useService } = require('@web/core/utils/hooks');

    // ──────────────────────────────────────────
    // Helpers
    // ──────────────────────────────────────────

    function fmtMoney(n) {
        if (!n) return '0 ₫';
        if (n >= 1e9) return (n / 1e9).toFixed(1) + ' tỷ ₫';
        if (n >= 1e6) return (n / 1e6).toFixed(1) + ' tr ₫';
        if (n >= 1e3) return (n / 1e3).toFixed(0) + ' k ₫';
        return n.toLocaleString('vi-VN') + ' ₫';
    }

    function badgeColor(s) {
        const map = {
            dang_lam: 'success', dang_su_dung: 'success', da_ghi_so: 'success',
            thu_viec: 'warning', cho_dua_vao_su_dung: 'warning', cho_duyet: 'warning',
            cho_truong_phong: 'warning', cho_ke_toan: 'warning', cho_giam_doc: 'warning',
            nghi_viec: 'danger', thanh_ly: 'secondary', bao_tri: 'info',
        };
        return map[s] || 'secondary';
    }

    async function ensureChartJs() {
        if (window.Chart) return;
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // ──────────────────────────────────────────
    // Dashboard Component
    // ──────────────────────────────────────────

    class DashboardTongHop extends Component {
        setup() {
            this.rpc = useService('rpc');
            this.action = useService('action');

            this.state = useState({
                loading: true,
                error: null,
                last_update: null,
                kpi: {},
                bang_nhanh: {},
            });

            this.charts = {};
            this.refreshTimer = null;

            this.canvasCpThang  = useRef('canvas_cp_thang');
            this.canvasNvPb     = useRef('canvas_nv_pb');
            this.canvasTsLoai   = useRef('canvas_ts_loai');
            this.canvasLuong12  = useRef('canvas_luong_12');
            this.canvasBtNguon  = useRef('canvas_bt_nguon');

            onMounted(async () => {
                await this._loadData();
                this._startAutoRefresh();
            });

            onWillUnmount(() => {
                this._stopAutoRefresh();
                this._destroyCharts();
            });
        }

        async _loadData() {
            try {
                this.state.loading = true;
                this.state.error = null;

                const result = await this.rpc('/web/dataset/call_kw', {
                    model: 'upg.dashboard',
                    method: 'get_all_kpi',
                    args: [],
                    kwargs: {},
                });

                this.state.kpi = result;
                this.state.last_update = new Date().toLocaleTimeString('vi-VN');
                this.state.loading = false;

                await this._renderAllCharts(result.charts || {});
            } catch (err) {
                console.error('[Dashboard] Load error:', err);
                this.state.error = 'Không thể tải dữ liệu. Vui lòng thử lại.';
                this.state.loading = false;
            }
        }

        _startAutoRefresh() {
            this.refreshTimer = setInterval(() => this._loadData(), 60000);
        }

        _stopAutoRefresh() {
            if (this.refreshTimer) {
                clearInterval(this.refreshTimer);
                this.refreshTimer = null;
            }
        }

        async _renderAllCharts(charts) {
            try { await ensureChartJs(); } catch (e) { return; }

            const mkChart = (key, el, cfg) => {
                if (this.charts[key]) this.charts[key].destroy();
                this.charts[key] = new window.Chart(el, cfg);
            };

            const moneyTip = (ctx) => `${ctx.dataset.label}: ${fmtMoney(ctx.raw)}`;

            if (charts.cp_thang && this.canvasCpThang.el) {
                mkChart('cp_thang', this.canvasCpThang.el, {
                    type: 'bar',
                    data: JSON.parse(charts.cp_thang),
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { title: { display: true, text: 'Chi Phí & Doanh Thu Theo Tháng' },
                                   tooltip: { callbacks: { label: moneyTip } } },
                        scales: { y: { ticks: { callback: v => fmtMoney(v) } } },
                    },
                });
            }
            if (charts.nv_phong_ban && this.canvasNvPb.el) {
                mkChart('nv_pb', this.canvasNvPb.el, {
                    type: 'pie',
                    data: JSON.parse(charts.nv_phong_ban),
                    options: { responsive: true, maintainAspectRatio: false,
                               plugins: { title: { display: true, text: 'Nhân Viên Theo Phòng Ban' }, legend: { position: 'right' } } },
                });
            }
            if (charts.ts_loai && this.canvasTsLoai.el) {
                mkChart('ts_loai', this.canvasTsLoai.el, {
                    type: 'doughnut',
                    data: JSON.parse(charts.ts_loai),
                    options: { responsive: true, maintainAspectRatio: false,
                               plugins: { title: { display: true, text: 'Tài Sản Theo Loại' }, legend: { position: 'right' } } },
                });
            }
            if (charts.luong_12thang && this.canvasLuong12.el) {
                mkChart('luong_12', this.canvasLuong12.el, {
                    type: 'line',
                    data: JSON.parse(charts.luong_12thang),
                    options: { responsive: true, maintainAspectRatio: false,
                               plugins: { tooltip: { callbacks: { label: moneyTip } } },
                               scales: { y: { ticks: { callback: v => fmtMoney(v) } } } },
                });
            }
            if (charts.bt_nguon && this.canvasBtNguon.el) {
                mkChart('bt_nguon', this.canvasBtNguon.el, {
                    type: 'pie',
                    data: JSON.parse(charts.bt_nguon),
                    options: { responsive: true, maintainAspectRatio: false,
                               plugins: { title: { display: true, text: 'Bút Toán: Tự Động vs Thủ Công' } } },
                });
            }
        }

        _destroyCharts() {
            Object.values(this.charts).forEach(c => c && c.destroy());
            this.charts = {};
        }

        fmtMoney(n)   { return fmtMoney(n); }
        badgeColor(s) { return badgeColor(s); }
        parseJson(str) { try { return JSON.parse(str || '[]'); } catch { return []; } }

        get nhanSu()   { return this.state.kpi.nhan_su   || {}; }
        get taiChinh() { return this.state.kpi.tai_chinh || {}; }
        get taiSan()   { return this.state.kpi.tai_san   || {}; }

        get topTaiSan()  { return this.parseJson(this.state.kpi.bang_nhanh && this.state.kpi.bang_nhanh.top_tai_san); }
        get nvMoi()      { return this.parseJson(this.state.kpi.bang_nhanh && this.state.kpi.bang_nhanh.nv_moi); }
        get btChoDuyet() { return this.parseJson(this.state.kpi.bang_nhanh && this.state.kpi.bang_nhanh.bt_cho_duyet); }
        get muaSamCd()   { return this.parseJson(this.state.kpi.bang_nhanh && this.state.kpi.bang_nhanh.mua_sam_cd); }

        async onRefresh() { await this._loadData(); }

        goTo(model) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: model,
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
            });
        }
    }

    DashboardTongHop.template = 'upgrade_project.DashboardTongHop';

    registry.category('actions').add('upg_dashboard_tong_hop', DashboardTongHop);

    return { DashboardTongHop };
});
