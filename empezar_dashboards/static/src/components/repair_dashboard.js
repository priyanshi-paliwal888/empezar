/** @odoo-module */

import { registry } from "@web/core/registry"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"
import { Component, onWillStart, onMounted, useState } from "@odoo/owl";


export class RepairDashboard extends Component {

    async GetAverageRepairTurnaroundTime() {
        let domain = [['repair_status', 'in', ['completed']]];
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)]);
        }
        if (this.state.ShippingLine1) {
            domain.push(['shipping_line_id', '=', parseInt(this.state.ShippingLine1)]);
        }
        if (this.state.TypeSize1) {
            domain.push(['pending_id.type_size_id', '=', parseInt(this.state.TypeSize1)]);
        }
        if (this.state.DateRange) {
            domain.push(['post_repair_date_and_time', '>=', this.state.DateRange.startDate]);
            domain.push(['post_repair_date_and_time', '<=', this.state.DateRange.endDate]);
        }
        else {
            let endDate = new Date();
            let firstDayOfMonth = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
            let startDate = `${firstDayOfMonth.getFullYear()}/${(firstDayOfMonth.getMonth() + 1).toString().padStart(2, '0')}/${firstDayOfMonth.getDate().toString().padStart(2, '0')}`;
            domain.push(['post_repair_date_and_time', '>=', startDate]);
            domain.push(['post_repair_date_and_time', '<=', endDate]);
        }
        const containers = await this.orm.searchRead(
            "repair.pending.estimates",
            domain,
            ["id", "location_id", "post_repair_date_and_time", "create_date"]
        );
        let locationMap = new Map();
        let locationCountMap = new Map();

        for (let container of containers) {
            const create_date = new Date(container.create_date);
            const repair_completion_date = new Date(container.post_repair_date_and_time);
            const diff = Math.abs(repair_completion_date - create_date);
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
            this.state.noData1 = true
        }
        else {
            this.state.noData1 = false
            this.state.AverageRepairTurnAroundTime = {
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

    async GetAverageEstimateAmount() {
        let domain = [['repair_status', 'in', ['approved', 'partially_approved', 'completed']]];
        const freq = this.state.freq;
        let startDate, endDate;
    
        if (this.state.DateRange?.startDate && this.state.DateRange?.endDate) {
            startDate = this.state.DateRange.startDate;
            endDate = this.state.DateRange.endDate;
            domain.push(['create_date', '>=', startDate]);
            domain.push(['create_date', '<=', endDate]);
        } else {
            endDate = new Date();
            let firstDayOfMonth = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
            startDate = `${firstDayOfMonth.getFullYear()}/${(firstDayOfMonth.getMonth() + 1).toString().padStart(2, '0')}/${firstDayOfMonth.getDate().toString().padStart(2, '0')}`;
            domain.push(['create_date', '>=', startDate]);
            domain.push(['create_date', '<=', endDate]);
        }
    
        const repairs = await this.orm.searchRead("repair.pending", domain, ["id", "location_id", "type_size_id", "create_date"]);
    
        let locationData = {};
        let locationLabels = [];
    
        for (const record of repairs) {
            const typeSizeData = await this.orm.searchRead(
                "container.type.data",
                [["id", "=", record.type_size_id[0]]],
                ["te_us"]
            );
            const teus = typeSizeData[0].te_us;
    
            const totalEstimateAmount = await this.orm.searchRead("repair.pending.estimates", [
                ['location_id', '=', record.location_id[1]],
                ['repair_status', 'in', ['approved', 'partially_approved', 'completed']],
                ['create_date', '>=', startDate],
                ['create_date', '<=', endDate]
            ], ["grand_total"]);
    
            const locationId = record.location_id[1];
            const createDate = new Date(record.create_date);
    
            let timePeriodKey = "";
            if (freq === "Monthly") {
                const month = createDate.getMonth();
                const year = createDate.getFullYear();
                timePeriodKey = `${locationId}-${year}-${month}`;
            } else if (freq === "Weekly") {
                const weekNumber = this.getWeekNumber(createDate);
                const year = createDate.getFullYear();
                timePeriodKey = `${locationId}-${year}-W${weekNumber}`;
            } else if (freq === "Yearly") {
                const year = createDate.getFullYear();
                timePeriodKey = `${locationId}-${year}`;
            }
    
            if (!locationData[timePeriodKey]) {
                locationData[timePeriodKey] = { totalTeUs: 0, totalAmount: 0 };
            }
            locationData[timePeriodKey].totalAmount = totalEstimateAmount.reduce((sum, estimate) => sum + estimate.grand_total, 0);
    
            locationData[timePeriodKey].totalTeUs += teus;
    
            if (!locationLabels.includes(locationId)) {
                locationLabels.push(locationId);
            }
        }
    
        let datasets = [];
        let months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        let timeLabels = [];
    
        if (freq === "Monthly") {
            timeLabels = months;
        } else if (freq === "Weekly") {
            for (const locationKey of Object.keys(locationData)) {
                const [locationId, year, week] = locationKey.split('-');
                if (!timeLabels.includes(`Week ${week}`)) {
                    timeLabels.push(`Week ${week}`);
                }
            }
        } else if (freq === "Yearly") {
            const years = new Set();
            for (const locationKey of Object.keys(locationData)) {
                const [locationId, year] = locationKey.split('-');
                years.add(year);
            }
            timeLabels = Array.from(years).sort();
        }
    
        for (const locationId of locationLabels) {
            let dataPoints = Array(timeLabels.length).fill(0);
            for (const [locationKey, data] of Object.entries(locationData)) {
                const [locId, year, period] = locationKey.split('-');
                if (locId === locationId) {
                    const average = data.totalAmount / data.totalTeUs;
                    let periodIndex = timeLabels.indexOf(freq === "Yearly" ? year : (freq === "Monthly" ? months[parseInt(period)] : `Week ${period}`));
                    dataPoints[periodIndex] = average;
                }
            }
            datasets.push({
                label: `${locationId}`,
                data: dataPoints,
                borderColor: this.getRandomColor(),
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
                fill: true,
                tension: 0.4,
                borderWidth: 2
            });
        }
    
        if (repairs.length === 0) {
            this.state.noData2 = true;
        } else {
            this.state.noData2 = false;
            this.state.AverageEstimateAmountDetails = {
                data: {
                    labels: timeLabels,
                    datasets: datasets
                }
            };
        }
    }

    getWeekNumber(date) {
        const startDate = new Date(date.getFullYear(), 0, 1);
        const days = Math.floor((date - startDate) / (24 * 60 * 60 * 1000));
        return Math.ceil((days + 1) / 7);
    }

    getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    async GetTotalAwaiting() {
        const totalAwaiting = await this.orm.searchCount("repair.pending", [['repair_status', 'in', ['awaiting_approval', 'awaiting_estimates']]]);
        this.state.TotalAwaiting = totalAwaiting;
    }

    async GetAwaitingEstimates() {
        const totalAwaitingEstimates = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'awaiting_estimates']]);
        this.state.TotalAwaitingEstimates = totalAwaitingEstimates;
    }

    async GetAwaitingApproval() {
        const totalAwaitingApproval = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'awaiting_approval']]);
        this.state.TotalAwaitingApproval = totalAwaitingApproval;
    }

    async GetTotalApproved() {
        const totalsApproved = await this.orm.searchCount("repair.pending", [['repair_status', 'in', ['approved', 'partially_approved']]]);
        this.state.TotalsApproved = totalsApproved;
    }

    async GetPartiallyApproved() {
        const totalPartiallyApproved = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'partially_approved']]);
        this.state.TotalPartiallyApproved = totalPartiallyApproved;
    }

    async GetApproved() {
        const totalApproved = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'approved']]);
        this.state.TotalApproved = totalApproved;
    }

    async GetRejected() {
        const totalRejected = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'rejected']]);
        this.state.TotalRejected = totalRejected;
    }

    async GetCompleted() {
        const TotalCompleted = await this.orm.searchCount("repair.pending", [['repair_status', '=', 'completed']]);
        this.state.TotalCompleted = TotalCompleted;
    }

    async GetTotalEstimateAmount() {
        const containers = await this.orm.searchRead("repair.pending", [], ["id", "location_id", "type_size_id"]);
        let TeUs = 0;
        for (const record of containers) {
            const typeSizeData = await this.orm.searchRead(
                "container.type.data",
                [["id", "=", record.type_size_id[0]]],
                ["te_us"]
            );
            TeUs += typeSizeData[0].te_us;
        }
        const locationIds = containers.map(container => container.location_id[0]);
        const totalEstimateAmount = await this.orm.searchRead("repair.pending.estimates", [
            ['location_id', 'in', locationIds],
            ['repair_status', 'in', ['approved', 'partially_approved', 'completed']]
        ], ["id", "location_id", "grand_total", "repair_status"]);

        const totalAmount = totalEstimateAmount.reduce((acc, estimate) => acc + estimate.grand_total, 0);
        const avgTotalEstimateAmount = parseFloat((totalAmount / TeUs).toFixed(2));
        this.state.AvgTotalEstimateAmount = avgTotalEstimateAmount;
        this.state.TotalEstimateAmount = totalAmount;
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

    async GetContainerByLocations() {
        let domain = this.prepareDomain();
        const containers = await this.orm.searchRead("repair.pending", domain, ["id", "location_id"]);
        const containerMap = new Map();
        containers.forEach(container => {
            const locationName = container.location_id[1];
            if (containerMap.has(locationName)) {
                containerMap.set(locationName, containerMap.get(locationName) + 1);
            } else {
                containerMap.set(locationName, 1);
            }
        });
        this.state.ContainerByLocations = containerMap;
        const totalContainers = containers.length;
        this.state.TotalContainer = totalContainers;
    }

    async GetTEUsByLocation() {
        let domain = this.prepareDomain();
        const repairRecords = await this.orm.searchRead("repair.pending", domain, ["id", "location_id", "type_size_id"]);
        const locationTeUsMap = {};
        for (const record of repairRecords) {
            const typeSizeData = await this.orm.searchRead(
                "container.type.data",
                [["id", "=", record.type_size_id[0]]],
                ["te_us"]
            );
            if (typeSizeData.length > 0) {
                const teUsValue = typeSizeData[0].te_us;
                const locationName = record.location_id[1];
                if (!locationTeUsMap[locationName]) {
                    locationTeUsMap[locationName] = 0;
                }
                locationTeUsMap[locationName] += teUsValue;
            }
        }
        this.state.TEUsByLocation = locationTeUsMap;
        const TeUsMap = new Map(Object.entries(locationTeUsMap));
        this.state.TEUsByLocation = TeUsMap;
        let totalTEUs = 0;
        for (let [key, value] of TeUsMap) {
            totalTEUs += parseInt(value);
        }
        this.state.TotalTEUsByLocation = totalTEUs;
    }

    async GetTotalEstAmtByLocation() {
        let domain = this.prepareDomain();
        const containers = await this.orm.searchRead("repair.pending", domain, ["id", "location_id", "pending_ids"]);
        const pendingIds = containers.map(container => container.pending_ids[0]);
        const estimates = await this.orm.searchRead("repair.pending.estimates", [
            ['id', '=', pendingIds],
            ['repair_status', 'in', ['approved', 'partially_approved', 'completed']]
        ], ["id", "location_id", "grand_total"]);
        const grandTotalMap = new Map();

        estimates.forEach(estimate => {
            const locationName = estimate.location_id[1];
            const grandTotal = estimate.grand_total;

            if (grandTotalMap.has(locationName)) {
                grandTotalMap.set(locationName, grandTotalMap.get(locationName) + grandTotal);
            } else {
                grandTotalMap.set(locationName, grandTotal);
            }
        });

        this.state.TotalEstAmtByLocation = grandTotalMap;
        let totalEstAmt = 0;
        for (let [key, value] of grandTotalMap) {
            totalEstAmt += parseInt(value);
        }
        this.state.GrandTotalEstAmtByLocation = totalEstAmt;
    }

    prepareDomain() {
        let domain = [['repair_status', 'in', ['approved', 'partially_approved', 'completed']]];
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)]);
        }
        if (this.state.ShippingLine1) {
            domain.push(['shipping_line_id', '=', parseInt(this.state.ShippingLine1)]);
        }
        if (this.state.TypeSize1) {
            domain.push(['type_size_id', '=', parseInt(this.state.TypeSize1)]);
        }
        if (this.state.DateRange) {
            domain.push(['create_date', '>=', this.state.DateRange.startDate]);
            domain.push(['create_date', '<=', this.state.DateRange.endDate]);
        }
        else {
            let endDate = new Date();
            let startDate = new Date(endDate.getFullYear(), endDate.getMonth(), 1);
            domain.push(['create_date', '>=', startDate]);
            domain.push(['create_date', '<=', endDate]);
        }
        return domain;
    }

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            freq: "Monthly",
        })

        onMounted(() => {
            $(function () {
                var today = new Date();
                var startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                var endDate = today;
                $('#dates').daterangepicker({
                    startDate: startDate,
                    endDate: endDate
                });
            });
            $('#dates').on('change', this.OnchangeDate.bind(this));
            $('.searchBtn').on('click', async () => {
                await Promise.all([
                    this.GetContainerByLocations(),
                    this.GetTEUsByLocation(),
                    this.GetTotalEstAmtByLocation(),
                    this.GetAverageRepairTurnaroundTime(),
                    this.GetAverageEstimateAmount(),
                ]);
            });
            $('.clearBtn').on('click', function (event) {
                location.reload();
            });
            $('.frequency-select').on('change', (event) => {
                this.state.freq = event.target.value;
                this.GetAverageEstimateAmount();
            });
        });

        onWillStart(async () => {
            await Promise.all([
                this.GetAverageRepairTurnaroundTime(),
                this.GetAverageEstimateAmount(),
                this.GetTotalAwaiting(),
                this.GetAwaitingEstimates(),
                this.GetAwaitingApproval(),
                this.GetTotalApproved(),
                this.GetPartiallyApproved(),
                this.GetApproved(),
                this.GetRejected(),
                this.GetCompleted(),
                this.GetTotalEstimateAmount(),
                this.GetShippingLine(),
                this.GetLocation(),
                this.GetType(),
                this.GetContainerByLocations(),
                this.GetTEUsByLocation(),
                this.GetTotalEstAmtByLocation(),
            ]);
        });
    }
}

RepairDashboard.components = { ChartRenderer }
RepairDashboard.template = "Empezar.RepairDashboard"
registry.category("actions").add("empezar.dashboard_repair", RepairDashboard)