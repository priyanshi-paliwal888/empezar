/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.disable_access = false;

    onWillStart(async () => {
        if (this.props.resModel === 'vessel.booking') {
            this.disable_access = await this.user.hasGroup("empezar_base.group_disable_vessel_booking");
        }
    });
},

getStaticActionMenuItems() {
    const menuItems = super.getStaticActionMenuItems();
    if (this.props.resModel === 'vessel.booking' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access;
            return result;
        };
    }

    return menuItems;
},
});