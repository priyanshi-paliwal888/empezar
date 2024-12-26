/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.disable_access_container_inventory = false;

    onWillStart(async () => {
        if (this.props.resModel === 'container.inventory') {
            this.disable_access_container_inventory = await this.user.hasGroup("empezar_base.group_disable_container_inventory");
        }
    });
},

getStaticActionMenuItems() {
    const menuItems = super.getStaticActionMenuItems();
    if (this.props.resModel === 'container.inventory' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_container_inventory;
            return result;
        };
    }

    return menuItems;
},
});