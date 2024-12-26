/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.disable_access_res_company = false;
        this.disable_access_lolo_charge = false;
        this.disable_access_container_facilities = false;
        this.disable_access_fiscal_year = false;
        this.disable_access_product_template = false;
        this.disable_access_port_data = false;
        this.disable_access_container_type_data = false;
        this.disable_access_hsn_code = false;
        this.disable_damage_condition = false;
        this.disable_hold_reason = false;
        this.disable_cancellation_reason = false;
        this.disable_res_partner = false;

    onWillStart(async () => {
        if (this.props.resModel === 'res.company') {
            this.disable_access_res_company = await this.user.hasGroup("empezar_base.group_disable_res_company");
        }
        else if (this.props.resModel === 'lolo.charge') {
            this.disable_access_lolo_charge = await this.user.hasGroup("empezar_base.group_disable_lolo_charges");
        }
        else if (this.props.resModel === 'container.facilities') {
            this.disable_access_container_facilities = await this.user.hasGroup("empezar_base.group_disable_container_facilities");
        }
        else if (this.props.resModel === 'account.fiscal.year') {
            this.disable_access_fiscal_year = await this.user.hasGroup("empezar_base.group_disable_container_master");
        }
        else if (this.props.resModel === 'product.template') {
            this.disable_access_product_template = await this.user.hasGroup("empezar_base.group_disable_charges");
        }
        else if (this.props.resModel === 'master.port.data') {
            this.disable_access_port_data = await this.user.hasGroup("empezar_base.group_port_data");
        }
        else if (this.props.resModel === 'container.type.data') {
            this.disable_access_container_type_data = await this.user.hasGroup("empezar_base.group_container_type");
        }
        else if (this.props.resModel === 'master.hsn.code') {
            this.disable_access_hsn_code = await this.user.hasGroup("empezar_base.group_hsn_sac_code");
        }
        else if (this.props.resModel === 'damage.condition') {
            this.disable_access_damage_condition = await this.user.hasGroup("empezar_base.group_damage_condition");
        }
        else if (this.props.resModel === 'hold.reason') {
            this.disable_access_hold_reason = await this.user.hasGroup("empezar_base.group_hold_reason");
        }
        else if (this.props.resModel === 'cancellation.reason') {
            this.disable_cancellation_reason = await this.user.hasGroup("empezar_base.group_cancellation_reason");
        }
//        else if (this.props.resModel === 'res.partner') {
//            this.disable_res_partner = await this.user.hasGroup("empezar_base.group_res_partner");
//        }
    });
},

getStaticActionMenuItems() {
    const menuItems = super.getStaticActionMenuItems();
    if (this.props.resModel === 'res.company' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_res_company;
            return result;
        };
    }
    else if (this.props.resModel === 'lolo.charge' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_lolo_charge;
            return result;
        };
    }
    else if (this.props.resModel === 'container.facilities' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_container_facilities;
            return result;
        };
    }
    else if (this.props.resModel === 'account.fiscal.year' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_fiscal_year;
            return result;
        };
    }
    else if (this.props.resModel === 'product.template' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_product_template;
            return result;
        };
    }
    else if (this.props.resModel === 'master.port.data' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_port_data;
            return result;
        };
    }
    else if (this.props.resModel === 'container.type.data' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_container_type_data;
            return result;
        };
    }
    else if (this.props.resModel === 'master.hsn.code' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_hsn_code;
            return result;
        };
    }
    else if (this.props.resModel === 'damage.condition' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_damage_condition;
            return result;
        };
    }
    else if (this.props.resModel === 'hold.reason' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_hold_reason;
            return result;
        };
    }
    else if (this.props.resModel === 'cancellation.reason' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_cancellation_reason;
            return result;
        };
    }

    return menuItems;
},
});