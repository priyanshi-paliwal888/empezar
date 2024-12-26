/** @odoo-module */

import { registry } from "@web/core/registry"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"
import { Component, onWillStart, onMounted, useState } from "@odoo/owl";

export class MovementDashboard extends Component {

    async GetMovement() {
        let domain_in = this.preparedDomain()
        let domain_out = this.preparedDomain()
        domain_in = this.getDateRange(domain_in, 'move_in_date_time');
        domain_out = this.getDateRange(domain_out, 'move_out_date_time');
        const move_in = await this.orm.readGroup("move.in", domain_in, ['location_id', 'shipping_line_id'], ['location_id'])
        const move_out = await this.orm.readGroup("move.out", domain_out, ['location_id', 'shipping_line_id'], ['location_id'])
        if (move_in.map(d => d.location_id[1]).length > 0) {
            var labels = move_in.map(d => d.location_id[1])
        }
        else {
            var labels = move_out.map(d => d.location_id ? d.location_id[1] : 'Unknown')
        }
        if (move_in.length == 0 && move_out.length == 0) {
            this.state.noData1 = true
        }
        else {
            this.state.noData1 = false
            this.state.MoveDetails = {
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Move IN',
                        data: move_in.map(d => d.location_id_count),
                        hoverOffset: 2,
                        barThickness: 30,
                        maxBarThickness: 30,
                        backgroundColor: 'rgb(136, 205, 235)',
                    },
                    {
                        label: 'Move Out',
                        data: move_out.map(d => d.location_id_count),
                        hoverOffset: 4,
                        barThickness: 30,
                        maxBarThickness: 30,
                        backgroundColor: 'rgb(251, 124, 115)',
                    }]
                },
            }
        }
    }

    async TypeMoveIn() {
        let domain = this.preparedDomain()
        domain = this.getDateRange(domain, 'move_in_date_time');
        const move_type_in = await this.orm.readGroup("move.in", domain, ['movement_type'], ['movement_type'], { orderby: "movement_type asc", lazy: false })
        if (move_type_in.length == 0) {
            this.state.noData2 = true
        }
        else {
            this.state.noData2 = false
            this.state.TypeMoveIn = {
                data: {
                    labels: move_type_in.map(d => `${d.movement_type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}`),
                    datasets: [{
                        label: 'Type Move IN',
                        data: move_type_in.map(d => d.__count),
                        backgroundColor: [
                            'rgb(254, 192, 203)',
                            'rgb(250, 128, 114)',
                            'rgb(136, 205, 235)',
                        ],
                    }],
                },
            }
        }
    }

    async TypeMoveOut() {
        let domain = this.preparedDomain()
        domain = this.getDateRange(domain, 'move_out_date_time');
        const move_type_out = await this.orm.readGroup("move.out", domain, ['movement_type'], ['movement_type'], { orderby: "movement_type asc", lazy: false })
        if (move_type_out.length == 0) {
            this.state.noData3 = true
        }
        else {
            this.state.noData3 = false
            this.state.TypeMoveOut = {
                data: {
                    labels: move_type_out.map(d => `${d.movement_type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}`),
                    datasets: [{
                        label: 'Type Move Out',
                        data: move_type_out.map(d => d.__count),
                        backgroundColor: [
                            'rgb(254, 192, 203)',
                            'rgb(250, 128, 114)',
                            'rgb(136, 205, 235)',
                        ],
                    }]
                },
            }
        }
    }

    async AverageTurnAroundTime() {
        let domain = [["active", "!=", "True"]]
        if (this.state.ShippingLine1) {
            domain.push(['move_in_id.shipping_line_id', '=', parseInt(this.state.ShippingLine1)])
        }
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)])
        }
        if (this.state.TypeSize1) {
            domain.push(['move_in_id.type_size_id', '=', parseInt(this.state.TypeSize1)])
        }
        domain = this.getDateRange(domain, 'move_in_date');
        const containers = await this.orm.searchRead(
            "container.inventory",
            domain, 
            ["id", "location_id", "move_in_id", "move_in_date", "move_out_date", "hour", "out_hour", "minutes", "out_minutes"]
        );
        
        let locationMap = new Map();
        let locationCountMap = new Map();
        
        for (let container of containers) {
            if (container.move_in_date && container.move_out_date) {
                const move_in_date = new Date(container.move_in_date);
                const move_out_date = new Date(container.move_out_date);
                const hour = parseFloat(container.hour);
                const minutes = parseFloat(container.minutes);
                const out_hour = parseFloat(container.out_hour);
                const out_minutes = parseFloat(container.out_minutes);
                const move_in_datetime = move_in_date.getTime() + hour * 3600 * 1000 + minutes * 60 * 1000;
                const move_out_datetime = move_out_date.getTime() + out_hour * 3600 * 1000 + out_minutes * 60 * 1000;
                const diff = Math.abs(move_out_datetime - move_in_datetime);
                const days = diff / (1000 * 60 * 60 * 24);
        
                if (container.location_id[1]) {
                    const locationName = container.location_id[1];
                    if (locationMap.has(locationName)) {
                        locationMap.set(locationName, locationMap.get(locationName) + days);
                    } else {
                        locationMap.set(locationName, days);
                    }
                    if (locationCountMap.has(locationName)) {
                        locationCountMap.set(locationName, locationCountMap.get(locationName) + 1);
                    } else {
                        locationCountMap.set(locationName, 1);
                    }
                }
            }
        }
        
        const transformedLocationMap = new Map(
            Array.from(locationMap.entries()).map(([location, totalDays]) => {
                const count = locationCountMap.get(location) || 1;
                const averageDays = totalDays / count;
                return [location, parseFloat(averageDays.toFixed(2))];
            })
        );
        const locationLabels = Array.from(transformedLocationMap.keys());
        const locationData = Array.from(transformedLocationMap.values());
        if (containers.length == 0) {
            this.state.noData6 = true
        }
        else {
            this.state.noData6 = false
            this.state.AverageTurnAroundTime = {
                data: {
                    labels: locationLabels,
                    datasets: [{
                        label: 'Location',
                        data: locationData,
                        hoverOffset: 2,
                        barThickness: 30,
                        maxBarThickness: 30,
                        backgroundColor: 'rgb(136, 205, 235)',
                    }]
                },
            };
        }
    }

    async DamageMoveIn() {
        let domain = this.preparedDomain()
        domain = this.getDateRange(domain, 'move_in_date_time');
        const damage_move_in = await this.orm.readGroup("move.in", domain, ['damage_condition'], ['damage_condition'])
        if (damage_move_in.length == 0) {
            this.state.noData4 = true
        }
        else {
            this.state.noData4 = false
            this.state.DamageMoveIn = {
                data: {
                    labels: damage_move_in.map(d => d.damage_condition[1]),
                    datasets: [{
                        label: 'Damage Move IN',
                        data: damage_move_in.map(d => d.damage_condition_count),
                        backgroundColor: [
                            'rgb(250, 128, 114)',
                            'rgb(135, 206, 235)',
                            'rgb(254, 192, 203)',
                            'rgb(165, 249, 166)',
                            'rgb(254, 192, 203)',
                            'rgb(136, 206, 235)',
                        ],
                    }]
                },
            }
        }
    }

    async GradeMoveIn() {
        let domain = this.preparedDomain()
        domain = this.getDateRange(domain, 'move_in_date_time');
        const grade_move_in = await this.orm.readGroup("move.in", domain, ['grade'], ['grade'])
        if (grade_move_in.length == 0) {
            this.state.noData5 = true
        }
        else {
            this.state.noData5 = false
            this.state.GradeMoveIn = {
                data: {
                    labels: grade_move_in.map(d => `Grade-${d.grade.toUpperCase()}`),
                    datasets: [{
                        label: 'Grade Move IN',
                        data: grade_move_in.map(d => d.grade_count),
                        backgroundColor: [
                            'rgb(250, 128, 114)',
                            'rgb(135, 206, 235)',
                            'rgb(254, 192, 203)',
                        ],
                    }]
                },
            }
        }
    }

    async GetShippingLine() {
        const shipping_lines = await this.orm.searchRead("res.partner", [['is_shipping_line', '=', 'True']], ["id", "name"]);
        this.state.ShippingLine = shipping_lines
    }

    async GetLocation() {
        const locations = await this.orm.searchRead("res.company", [], ["id", "name"]);
        this.state.Locations = locations
    }

    async GetType() {
        const types = await this.orm.searchRead("container.type.data", [], ["id", "name", "company_size_type_code"]);
        this.state.Types = types
    }

    async OnchangeShippingLine(ev) {
        this.state.ShippingLine1 = ev.target.value;
    }

    async OnchangeLocation(ev) {
        this.state.Location1 = ev.target.value;
    }

    async OnchangeTypeSize(ev) {
        this.state.TypeSize1 = ev.target.value;
    }

    async OnchangeDate(ev) {
        const dateRange = ev.target.value.split(' - ');
        this.state.DateRange = {
            startDate: dateRange[0],
            endDate: dateRange[1]
        };
    }

    preparedDomain() {
        let domain = []
        if (this.state.ShippingLine1) {
            domain.push(['shipping_line_id', '=', parseInt(this.state.ShippingLine1)])
        }
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)])
        }
        if (this.state.TypeSize1) {
            domain.push(['type_size_id', '=', parseInt(this.state.TypeSize1)])
        }
        return domain
    }

    getDateRange(domain, dateField) {
        if (this.state.DateRange) {
            domain.push([dateField, '>=', this.state.DateRange.startDate]);
            domain.push([dateField, '<=', this.state.DateRange.endDate]);
        } else {
            let endDate = new Date();
            let startDate = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
            domain.push([dateField, '>=', startDate]);
            domain.push([dateField, '<=', endDate]);
        }
        return domain;
    }
    
    setup() {
        this.orm = useService("orm");
        this.state = useState({})

        onMounted(() => {
            $(function() {
                var today = new Date();
                var startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                var endDate = today;
                $('#dates').daterangepicker({
                    startDate: startDate,
                    endDate: endDate
                });
            });
            $('#dates').on('change', this.OnchangeDate.bind(this));
            $('.clearBtn').on('click', function (event) {
                location.reload();
            });
            $('.searchBtn').on('click', async () => {
                await Promise.all([
                    this.GetMovement(),
                    this.TypeMoveIn(),
                    this.TypeMoveOut(),
                    this.DamageMoveIn(),
                    this.GradeMoveIn(),
                    this.AverageTurnAroundTime()
                ]);
            });
        });

        onWillStart(async () => {
            await Promise.all([
                this.GetMovement(),
                this.TypeMoveIn(),
                this.TypeMoveOut(),
                this.AverageTurnAroundTime(),
                this.DamageMoveIn(),
                this.GradeMoveIn(),
                this.GetShippingLine(),
                this.GetLocation(),
                this.GetType()
            ]);

        });
    }
}

MovementDashboard.components = { ChartRenderer }
MovementDashboard.template = "Empezar.MovementDashboard"

registry.category("actions").add("empezar.dashboard_movement", MovementDashboard)