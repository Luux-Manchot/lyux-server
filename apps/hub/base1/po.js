/* Shim de traduction : les plugins restent en francais, pas de catalogue externe. */
(function () {
    "use strict";
    window.po = window.po || function () {
        return { gettext: function (message) { return message; } };
    };
})();
