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
        this.dialogService = useService("dialog"); // useService to access the dialog
        this.orm = useService("orm");
    },

    async onRecordSaved(record) {
        if (this.props.resModel === 'repair.pending') {
            const recContainer = record.data.container_no;
            const recShippingLine = record.data.shipping_line_id[0];
            const recTypeSize = record.data.type_size_id[0];
            const recProductionMonth = record.data.month;
            const recProductionYear = record.data.year;
            const recGrossWt = record.data.gross_wt;
            const recTareWt = record.data.tare_wt;

            const domain = [['name', '=', recContainer]]; // Example domain
            const fields = ['shipping_line_id', 'type_size', 'month', 'year', 'gross_wt', 'tare_wt'];

            const viewObjects = await this.orm.call("container.master", "search_read", [domain], {
                fields: fields,
                limit: 1 // Applying limit=1
            });

            if (viewObjects.length > 0) {
                const masterObj = viewObjects[0];
                const masterShippingLine = masterObj.shipping_line_id[0];
                const masterTypeSize = masterObj.type_size[0];
                const masterMonth = masterObj.month;
                const masterYear = masterObj.year;
                const masterGrossWt = masterObj.gross_wt;
                const masterTareWt = masterObj.tare_wt;

                if (
                    (recShippingLine && masterShippingLine && recShippingLine !== masterShippingLine) ||
                    (recTypeSize && masterTypeSize && recTypeSize !== masterTypeSize) ||
                    (recProductionMonth && masterMonth && recProductionMonth !== masterMonth) ||
                    (recProductionYear && masterYear && recProductionYear !== masterYear) ||
                    (recGrossWt && masterGrossWt && parseInt(recGrossWt) !== masterGrossWt) ||
                    (recTareWt && masterTareWt && parseInt(recTareWt) !== masterTareWt)
                ) {
                    this.dialogService.add(ConfirmationDialog, {
                        title: _t("Update Confirmation In Container Master"),
                        body: _t("The container details entered do not match the container master records. Changing this will update the container details in the master."),
                        confirm: async () => {
                            await super.onRecordSaved(...arguments); // Call the parent method
                            try {
                                await this.orm.call('repair.pending', 'update_container_master', [recContainer, recShippingLine,
                                recTypeSize, recProductionMonth, recProductionYear, recGrossWt, recTareWt]);
                            } catch (error) {
                                console.error('Error while updating container master:', error);
                            }
                        },
                        confirmLabel: _t("Yes, Update"),
                        cancel: async () => {
                            await super.onRecordSaved(...arguments); // Call the parent method
                        },
                        cancelLabel: _t("No"),
                    });
                } else {
                    // Proceed with saving the record if no matching record is found
                    await super.onRecordSaved(...arguments); // Call the parent method
                }
            } else {
                // Proceed with saving the record if no matching record is found
                await super.onRecordSaved(...arguments); // Call the parent method
            }
        } else {
            // Call the parent method if not in 'repair.pending' model
            await super.onRecordSaved(...arguments);
        }
    },
});
