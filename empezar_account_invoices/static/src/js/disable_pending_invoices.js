/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { onWillStart } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.disable_access_pending_invoices = false;
        this.disable_access_monthly_lock = false;

    onWillStart(async () => {
        if (this.props.resModel === 'pending.invoices') {
            this.disable_access_pending_invoices = await this.user.hasGroup("empezar_base.group_disable_pending_invoices");
        }
        else if (this.props.resModel === 'monthly.lock') {
            this.disable_access_monthly_lock = await this.user.hasGroup("empezar_base.group_disable_monthly_lock");
        }
    });
},

getStaticActionMenuItems() {
    const menuItems = super.getStaticActionMenuItems();
    if (this.props.resModel === 'pending.invoices' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_pending_invoices;
            return result;
        };
    }
    else if (this.props.resModel === 'monthly.lock' && menuItems.archive) {
        const originalIsAvailable = menuItems.archive.isAvailable;

        menuItems.archive.isAvailable = () => {
            const result = originalIsAvailable() && this.disable_access_monthly_lock;
            return result;
        };
    }

    return menuItems;
},
});