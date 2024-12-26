/** @odoo-module */

import { registry } from "@web/core/registry"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"
import { Component, onWillStart, onMounted, useState } from "@odoo/owl";

export class InventoryDashboard extends Component {

    async GetInventory() {
        let domain = await this.buildDomain(this.state);
        domain = this.getDate(domain, 'move_in_date');
        const inventory = await this.orm.searchRead("container.inventory", domain, ["id", "location_id", "status"]);
        const locationStatusCounts = {};
        inventory.forEach((item) => {
            const location = item.location_id[1];
            const status = item.status;
            if (!locationStatusCounts[location]) {
                locationStatusCounts[location] = {};
            }
            if (!locationStatusCounts[location][status]) {
                locationStatusCounts[location][status] = 0;
            }
            locationStatusCounts[location][status] += 1;
        });
        const locations = Object.keys(locationStatusCounts);

        if (locations.length == 0) {
            this.state.noRecord1 = true
        }
        else {
            this.state.noRecord1 = false
            this.state.InventoryDetails = {
                data: {
                    labels: locations,
                    datasets: [
                        {
                            label: 'Awaiting Estimates',
                            data: locations.map(location => locationStatusCounts[location]['ae'] || 0),
                            barThickness: 30,
                            maxBarThickness: 30,
                            backgroundColor: 'rgb(255, 99, 132)',
                        },
                        {
                            label: 'Awaiting Approval',
                            data: locations.map(location => locationStatusCounts[location]['aa'] || 0),
                            barThickness: 30,
                            maxBarThickness: 30,
                            backgroundColor: 'rgb(255, 159, 64)',
                        },
                        {
                            label: 'Awaiting Repair',
                            data: locations.map(location => locationStatusCounts[location]['ar'] || 0),
                            barThickness: 30,
                            maxBarThickness: 30,
                            backgroundColor: 'rgb(255, 205, 86)',
                        },
                        {
                            label: 'Available',
                            data: locations.map(location => locationStatusCounts[location]['av'] || 0),
                            barThickness: 30,
                            maxBarThickness: 30,
                            backgroundColor: 'rgb(75, 192, 192)',
                        },
                        {
                            label: 'Direct Available (DAV)',
                            data: locations.map(location => locationStatusCounts[location]['dav'] || 0),
                            barThickness: 30,
                            maxBarThickness: 30,
                            backgroundColor: 'rgb(54, 162, 235)',
                        },
                    ],
                },
            }
        }
    }

    async GetLocationShippingLineData() {
        let domain = await this.buildDomain(this.state);
        domain = this.getDate(domain, 'move_in_date');
        const location_shipping_line_data = await this.orm.searchRead(
            "container.inventory",
            domain,
            ["id", "location_id", "name"]
        );

        let locationShippingLineMap = {};
        for (const record of location_shipping_line_data) {
            const containerMasterData = await this.orm.searchRead(
                "container.master",
                [["name", "=", record.name]],
                ["id", "shipping_line_id"]
            );
            if (!locationShippingLineMap[record.location_id]) {
                locationShippingLineMap[record.location_id] = {};
            }
            for (const data of containerMasterData) {
                const shippingLineId = data.shipping_line_id;
                if (shippingLineId) {
                    if (!locationShippingLineMap[record.location_id][shippingLineId]) {
                        locationShippingLineMap[record.location_id][shippingLineId] = 0;
                    }
                    locationShippingLineMap[record.location_id][shippingLineId] += 1;
                }
            }
        }
        const result = Object.entries(locationShippingLineMap).map(([locationId, shippingLines]) => ({
            location_id: locationId,
            shipping_lines: Object.entries(shippingLines).map(([shippingLineId, count]) => ({
                shipping_line_id: shippingLineId,
                count: count
            }))
        }));
        this.state.LocationShippingLineData = result;
    }

    async fetchPartnerAddresses() {
        let domain = await this.buildDomain(this.state);
        domain = this.getDate(domain, 'move_in_date');
        const records = await this.orm.readGroup("container.inventory", domain, ["location_id"], ["location_id"]);
        const partners = await this.orm.searchRead('res.company', [['name', 'in', records.map(record => record.location_id[1])]], ['street', 'street2', 'city', 'state_id', 'country_id']);
        const addresses = partners.map(partner => {
            const addressParts = [partner.city, partner.country_id[1]].filter(Boolean);
            return addressParts.join(", ");
        }).filter(Boolean);
        const counts = records.map(r => r.location_id_count);
        this.mapConfig.count = counts;
        this.mapConfig.addresses = addresses;
    }

    initializeMap() {
        const { lat, long, addresses, count } = this.mapConfig;

        if (!addresses) {
            console.log("No addresses found.");
            return;
        }
        else {
            console.log("success", addresses);
        }
        if (!count) {
            console.log("No counts found.");
        }
        else {
            console.log("success", count);
        }
        const uluru = { lat: lat, lng: long };
        const map = new google.maps.Map(document.getElementById("googleMap"), {
            zoom: 5,
            center: uluru,
        });
        addresses.forEach((address, index) => {
            const geocoder = new google.maps.Geocoder();
            geocoder.geocode({ address }, (results, status) => {
                if (status === google.maps.GeocoderStatus.OK) {
                    new google.maps.Marker({
                        position: results[0].geometry.location,
                        map: map,
                        title: address,
                        label: {
                            text: `${count[index]}`,
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold',
                        },
                    });
                } else {
                    console.error("Geocode failed for the following address: " + address);
                }
            });
        });
    }

    async GetContainerAgeingAnalysis() {
        const as_on_date = new Date();
        let domain = [["move_in_date", "<=", as_on_date]];
        if (this.state.ShippingLine1) {
            const masterNames = await this.orm.searchRead(
                "container.master",
                [["shipping_line_id", "=", parseInt(this.state.ShippingLine1)]],
                ["name"]
            ).then(results => results.map(master => master.name));
            domain.push(["name", "in", masterNames]);
        }
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)])
        }
        if (this.state.TypeSize1) {
            const masterNames = await this.orm.searchRead(
                "container.master",
                [["type_size", "=", parseInt(this.state.TypeSize1)]],
                ["name"]
            ).then(results => results.map(master => master.name));
            domain.push(["name", "in", masterNames]);
        }
        if (this.state.AsOnDate) {
            domain.push(["move_in_date", "<=", this.state.AsOnDate]);
        }
        const containers = await this.orm.searchRead(
            "container.inventory",
            domain,
            ["id", "location_id", "move_in_date"]
        );
        let locationDaysMap = new Map();
        let locationCountMap = new Map();

        for (let container of containers) {
            if (container.move_in_date) {
                const move_in_date = new Date(container.move_in_date);
                const diff_date = as_on_date - move_in_date;
                const days = Math.floor(diff_date / (1000 * 60 * 60 * 24));

                if (container.location_id[1]) {
                    const locationName = container.location_id[1];
                    if (locationDaysMap.has(locationName)) {
                        locationDaysMap.set(locationName, locationDaysMap.get(locationName) + days);
                    } else {
                        locationDaysMap.set(locationName, days);
                    }
                    if (locationCountMap.has(locationName)) {
                        locationCountMap.set(locationName, locationCountMap.get(locationName) + 1);
                    } else {
                        locationCountMap.set(locationName, 1);
                    }
                }
            }
        }
        const result = Array.from(locationDaysMap.entries()).map(([location, days]) => ({
            location: location,
            average: days / locationCountMap.get(location)
        }));
        if (result.length == 0) {
            this.state.noRecord3 = true
        }
        else {
            this.state.noRecord3 = false
            this.state.ContainerAgeingAnalysis = {
                data: {
                    labels: result.map(d => d.location),
                    datasets: [{
                        label: 'DAYS',
                        data: result.map(d => d.average),
                        hoverOffset: 2,
                        barThickness: 30,
                        maxBarThickness: 30,
                        backgroundColor: 'rgb(136, 205, 235)',
                    }]
                },
            }
        }
    }

    async GetContainerHoldAnalysis() {
        let domain = [];
        if (this.state.ShippingLine1) {
            const masterNames = await this.orm.searchRead(
                "container.master",
                [["shipping_line_id", "=", parseInt(this.state.ShippingLine1)]],
                ["name"]
            ).then(results => results.map(master => master.name));
            domain.push(["inventory_id", "in", masterNames]);
        }
        if (this.state.Location1) {
            domain.push(['location_id', '=', parseInt(this.state.Location1)])
        }
        if (this.state.TypeSize1) {
            domain.push(['type_size', '=', parseInt(this.state.TypeSize1)])
        }
        if (this.state.AsOnDate) {
            domain.push(["hold_date", "<=", this.state.AsOnDate]);
        }
        else {
            domain.push(["hold_date", "<=", new Date()]);
        }
        const hold_release_containers = await this.orm.readGroup("hold.release.containers", domain, ['hold_reason_id'], ['hold_reason_id'], { orderby: "hold_reason_id asc", lazy: false })

        if (hold_release_containers.length == 0) {
            this.state.noRecord4 = true
        }
        else {
            this.state.noRecord4 = false
            this.state.ContainerHoldAnalysis = {
                data: {
                    labels: hold_release_containers.map(d => d.hold_reason_id[1]),
                    datasets: [{
                        label: 'Container Hold',
                        data: hold_release_containers.map(d => d.__count),
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

    async GetYardOccupancy() {
        let domain = await this.buildDomain(this.state);
        domain = this.getDate(domain, 'move_in_date');
        const inventoryRecords = await this.orm.searchRead(
            "container.inventory",
            domain,
            ["id", "location_id", "name"]
        );
        const locationTeUsMap = {};
        for (const record of inventoryRecords) {
            const containerMasterData = await this.orm.searchRead(
                "container.master",
                [["name", "=", record.name]],
                ["id", "type_size"]
            );
            const typeSizeId = containerMasterData[0].type_size[0];

            const typeSizeData = await this.orm.searchRead(
                "container.type.data",
                [["id", "=", typeSizeId]],
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
        const capacity_data = await this.orm.searchRead("res.company", [], ["id", "name", "capacity"]);
        const locationCapacityMap = {};
        for (const record of capacity_data) {
            locationCapacityMap[record.name] = record.capacity;
        }
        const YardOccupancy = {}
        for (const [location, teUs] of Object.entries(locationTeUsMap)) {
            const capacity = locationCapacityMap[location];
            YardOccupancy[location] = teUs / capacity * 100;
        }
        if (Object.keys(YardOccupancy).length == 0) {
            this.state.noRecord5 = true
        }
        else {
            this.state.noRecord5 = false
            this.state.YardOccupancyAnalysis = {
                data: {
                    labels: Object.keys(YardOccupancy),
                    datasets: [{
                        label: 'Location',
                        data: Object.values(YardOccupancy),
                        hoverOffset: 2,
                        barThickness: 30,
                        maxBarThickness: 30,
                        backgroundColor: 'rgb(136, 205, 235)',
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
        this.state.AsOnDate = ev.target.value;
    }

    async buildDomain(filters) {
        let domain = [];
        if (filters.ShippingLine1) {
            const masterNames = await this.orm.searchRead(
                "container.master",
                [["shipping_line_id", "=", parseInt(filters.ShippingLine1)]],
                ["name"]
            ).then(results => results.map(master => master.name));
            domain.push(["name", "in", masterNames]);
        }
        if (filters.Location1) {
            domain.push(['location_id', '=', parseInt(filters.Location1)]);
        }
        if (filters.TypeSize1) {
            const masterNames = await this.orm.searchRead(
                "container.master",
                [["type_size", "=", parseInt(filters.TypeSize1)]],
                ["name"]
            ).then(results => results.map(master => master.name));
            domain.push(["name", "in", masterNames]);
        }
        return domain;
    }

    getDate(domain, dateField) {
        if (this.state.AsOnDate) {
            domain.push([dateField, "<=", this.state.AsOnDate]);
        } else {
            domain.push([dateField, "<=", new Date()]);
        }
        return domain;
    }

    setup() {
        this.orm = useService("orm");
        this.state = useState({})
        this.mapConfig = {
            lat: 20.5937,
            long: 78.9629,
            addresses: [],
            count: [],
        };

        onMounted(() => {
            $(function () {
                var today = new Date();
                var AsOnDate = today.toISOString().substr(0, 10);
                $("input[type='date']").val(AsOnDate);
            })
            $('.clearBtn').on('click', function (event) {
                location.reload();
            });
            $('.searchBtn').on('click', async () => {
                await Promise.all([
                    this.GetInventory(),
                    this.GetLocationShippingLineData(),
                    this.fetchPartnerAddresses(),
                    this.GetContainerAgeingAnalysis(),
                    this.GetContainerHoldAnalysis(),
                    this.GetYardOccupancy(),
                ]);
                this.initializeMap();
            });
            this.initializeMap();
        });

        onWillStart(async () => {
            await Promise.all([
                this.fetchPartnerAddresses(),
                this.GetInventory(),
                this.GetLocationShippingLineData(),
                this.GetContainerAgeingAnalysis(),
                this.GetContainerHoldAnalysis(),
                this.GetYardOccupancy(),
                this.GetShippingLine(),
                this.GetLocation(),
                this.GetType(),
            ]);
        });
    }
}

InventoryDashboard.components = { ChartRenderer }
InventoryDashboard.template = "Empezar.InventoryDashboard"
registry.category("actions").add("empezar.dashboard_inventory", InventoryDashboard)
const script = document.createElement("script");
script.src = "https://maps.googleapis.com/maps/api/js?key=AIzaSyCFFqySePr9frroT5m96cNa2JcJLLCf7f0";
script.defer = true;
script.onload = () => console.log("Google Maps API loaded");
document.head.appendChild(script);