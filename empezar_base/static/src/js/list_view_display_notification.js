/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from "@web/views/list/list_controller";
import { _t } from "@web/core/l10n/translation";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { onMounted } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },

async onRecordSaved(record) {
    if (this.props.resModel == 'ir.model.access'){
                var message = 'Permissions saved successfully.'
                this.notification.add(_t(message), {
                    title: _t("Success"),
                    type: "success",
                });
                return true;
            }
}
});
