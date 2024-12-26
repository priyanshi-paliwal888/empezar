/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class BooleanEyeField extends Component {
    static template = "BooleanEyeField";
    static props = {
        ...standardFieldProps,
        icon: { type: String, optional: true },
        label: { type: String, optional: true },
        autosave: { type: Boolean, optional: true },
    };
    static defaultProps = {
        icon: "fa-eye",
    };

    update() {
        if (!this.props.record.data[this.props.name]){
            $('div').find('div[name="new_passwd"] input').attr('type', 'text');
            $('div').find('div[name="confirm_passwd"] input').attr('type', 'text');
        }
        else{
            $('div').find('div[name="new_passwd"] input').attr('type', 'password');
            $('div').find('div[name="confirm_passwd"] input').attr('type', 'password');
        }
        this.props.record.update({ [this.props.name]: !this.props.record.data[this.props.name] });
    }
}

export const booleanEyeField = {
    component: BooleanEyeField,
    displayName: _t("Boolean Eye"),
    supportedOptions: [
        {
            label: _t("Eye"),
            name: "icon",
            type: "string",
        },
    ],
    supportedTypes: ["boolean"],
    extractProps: ({ options, string }) => ({
        icon: options.icon,
        label: string,
    }),
};

registry.category("fields").add("boolean_eye", booleanEyeField);
