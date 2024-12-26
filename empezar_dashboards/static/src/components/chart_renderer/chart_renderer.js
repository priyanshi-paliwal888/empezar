/** @odoo-module */

import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, useEffect, onMounted, onWillUnmount } = owl

export class ChartRenderer extends Component {
    setup() {
        this.chartRef = useRef("chart");

        onMounted(() => this.renderChart());
        useEffect(() => {
            this.renderChart();
        }, () => [this.props.config]);

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }

        const totalPlugin = {
            id: 'totalPlugin',
            beforeDraw(chart) {
                if (chart.config.type === 'doughnut') {
                    const { width } = chart;
                    const { height } = chart;
                    const ctx = chart.ctx;
                    ctx.restore();
                    const total = chart.config.data.datasets[0].data.reduce((acc, val) => acc + val, 0);
                    const label = chart.config.options.plugins.customLabel || 'Total';
                    ctx.font = `${(height / 250).toFixed(2)}em sans-serif`;
                    ctx.textBaseline = 'middle';
                    ctx.textAlign = 'center';
                    const centerX = width / 2;
                    const centerY = height / 2;
                    ctx.fillStyle = 'grey';
                    ctx.fillText(label, centerX + 15, centerY - 30);
                    ctx.font = `${(height / 100).toFixed(2)}em sans-serif`;
                    ctx.fillStyle = 'black';
                    ctx.fillText(total, centerX + 15, centerY + 10);
                    ctx.save();
                }
            }
        };

        this.chart = new Chart(this.chartRef.el, {
            type: this.props.type,
            data: this.props.config.data,
            options: {
                cutout: '60%',
                indexAxis: this.props.indexAxis,
                responsive: true,
                maintainAspectRatio: false,
                x: {
                    stacked: this.props.stackX,
                },
                y: {
                    stacked: this.props.stackY,
                },
                plugins: {
                    customLabel: this.props.label,
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 8,
                            boxHeight: 8,
                        },
                    },
                    title: {
                        display: true,
                        text: this.props.title,
                        position: 'left',
                    },
                }
            },
            plugins: [totalPlugin],
        });
    }
}

ChartRenderer.template = "empezar.ChartRenderer"
