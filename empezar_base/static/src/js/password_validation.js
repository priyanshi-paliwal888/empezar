/* @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { _t } from "@web/core/l10n/translation";
import { useAutofocus, useService } from "@web/core/utils/hooks";

patch(FormRenderer.prototype, {

    setup(parent, model, renderer, params) {
        super.setup();
        var self = this;
        $(document).on('keyup', '.custom_password', function () { self._custom_password() });
        $(document).on('keyup', '.custom_confirm_password', function () { self._custom_password() });
        $(document).on('click', '.custom_password', function () { self._onclick_pwd() });
        $(document).on('click', '.o_data_row', function () { self._onclick_data() });
    },

    init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
        },

    _render: function () {
            var self = this;
            return this._super.apply(this, arguments);
        },

        _onclick_pwd: function (){
            document.getElementsByClassName('custom_password')
            document.getElementById("message").style.display = "block";
            if(document.getElementById("letter").classList.contains('valid') &&
              document.getElementById("capital").classList.contains('valid') &&
              document.getElementById("number").classList.contains('valid') &&
              document.getElementById("special").classList.contains('valid') &&
              document.getElementById("length").classList.contains('valid') &&
              document.getElementById("match").classList.contains('valid'))
            {
              document.getElementById("custom_password").removeAttribute("disabled");
            }
            else{
              document.getElementById("custom_password").setAttribute('disabled', true);
            }
        },

        _onclick_data: function (){
            if(document.getElementsByClassName('toggle_show_password') && document.getElementsByClassName('toggle_show_password')[0]){
                if(document.getElementsByClassName('toggle_show_password')[0].hasAttribute('disabled')){
                    document.getElementsByClassName('toggle_show_password')[0].removeAttribute("disabled");
                }

            }
        },

        _custom_password: function (ev) {
              document.getElementById("custom_password").setAttribute('disabled', true);
              var lowerCaseLetters = /[a-z]/g;
              if(document.querySelector('div.custom_password').firstElementChild.value.match(lowerCaseLetters)){
                    document.getElementById("letter").classList.remove("invalid");
                    document.getElementById("letter").classList.add("valid")
              }
              else{
                document.getElementById("letter").classList.remove("valid");
                document.getElementById("letter").classList.add("invalid");
              }

              var upperCaseLetters = /[A-Z]/g;
              if(document.querySelector('div.custom_password').firstElementChild.value.match(upperCaseLetters)) {
                document.getElementById("capital").classList.remove("invalid");
                document.getElementById("capital").classList.add("valid");
              } else {
                document.getElementById("capital").classList.remove("valid");
                document.getElementById("capital").classList.add("invalid");
              }

              // Validate numbers
              var numbers = /[0-9]/g;
              if(document.querySelector('div.custom_password').firstElementChild.value.match(numbers)) {
                document.getElementById("number").classList.remove("invalid");
                document.getElementById("number").classList.add("valid");
              } else {
                document.getElementById("number").classList.remove("valid");
                document.getElementById("number").classList.add("invalid");
              }

              // Validate length
              if(document.querySelector('div.custom_password').firstElementChild.value.length >= 8) {
                document.getElementById("length").classList.remove("invalid");
                document.getElementById("length").classList.add("valid");
              } else {
                document.getElementById("length").classList.remove("valid");
                document.getElementById("length").classList.add("invalid");
              }


              const specialChars1 = '[`!@#$%^&*()_+-=[]{};\':"\\|,.<>/?~]/';
              if(specialChars1.split('').some((specialChar2) => document.querySelector('div.custom_password').firstElementChild.value.includes(specialChar2))){
                 document.getElementById("special").classList.remove("invalid");
                 document.getElementById("special").classList.add("valid");
              }
              else{
                document.getElementById("special").classList.remove("valid");
                document.getElementById("special").classList.add("invalid");
              }

              if(document.querySelector('div.custom_confirm_password').firstElementChild && document.querySelector('div.custom_password').firstElementChild && document.querySelector('div.custom_password').firstElementChild.value == document.querySelector('div.custom_confirm_password').firstElementChild.value){

                      document.getElementById("match").classList.remove("invalid");
                      document.getElementById("match").classList.add("valid");


                    if(document.getElementById("letter").classList.contains('valid') && document.getElementById("capital").classList.contains('valid') &&
                      document.getElementById("number").classList.contains('valid') &&
                      document.getElementById("special").classList.contains('valid') &&
                      document.getElementById("length").classList.contains('valid') &&
                      document.getElementById("match").classList.contains('valid')){
                        document.getElementById("custom_password").removeAttribute("disabled");
                      }
                      else{
                        document.getElementById("custom_password").setAttribute('disabled', true);
                      }


//                  hasClass
              }
              else{
                  document.getElementById("match").classList.remove("valid");
                  document.getElementById("match").classList.add("invalid");
              }
        },
});