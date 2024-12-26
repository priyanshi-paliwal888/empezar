/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.dialogService = useService("dialog"); 
        this.orm = useService("orm");
    },

    async onWillSaveRecord(record, changes) {
        if (this.props.resModel === 'move.out') {
            const containerStatus = record.data.container_status;

            if (containerStatus !== 'av') {

                return new Promise((resolve) => {
                    this.dialogService.add(ConfirmationDialog, {
                        title: _t("Container Status Confirmation"),
                        body: _t(`Container is not in ‘Available’ status, Do you still want to continue?`),
                        confirm: () => {
                            resolve(true);  // Proceed with saving if "Yes" is selected
                        },
                        cancel: () => {
                            resolve(false); // Prevent save if "No" is selected
                        },
                        confirmLabel: _t("Yes"),
                        cancelLabel: _t("No"),
                    });
                });
            }
        }
        return super.onWillSaveRecord(record, changes); // Continue if not in 'repair.pending' model
    }
});
