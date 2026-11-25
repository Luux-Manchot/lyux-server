/*
 * Shim Cockpit pour le conteneur lyux-hub.
 *
 * Les plugins de apps/cockpit/ restent installables tels quels dans Cockpit
 * (qui fournit son propre ../base1/cockpit.js). Ici, on ne reproduit que
 * l'API utilisée par les plugins : location, onlocationchanged et file().
 *
 * Aucun accès au /etc de l'hote n'est donne au conteneur : file().read()
 * retourne une chaine vide. Le plugin "users" reste donc Heritage (natif).
 */
(function () {
    "use strict";

    // Les plugins detectent cette variable pour choisir l'API relative /api.
    window.LYUX_API_BASE = "/api";

    function parsePath(hash) {
        var raw = String(hash || "").replace(/^#\/?/, "");
        return raw ? raw.split("/") : [];
    }

    var locationState = {
        path: parsePath(window.location.hash),
        go: function (parts) {
            locationState.path = Array.isArray(parts) ? parts.slice() : [parts];
            window.location.hash = "/" + locationState.path.join("/");
            emitChange();
        }
    };

    function emitChange() {
        if (typeof window.cockpit.onlocationchanged === "function") {
            window.cockpit.onlocationchanged();
        }
    }

    window.addEventListener("hashchange", function () {
        locationState.path = parsePath(window.location.hash);
        emitChange();
    });

    window.cockpit = {
        location: locationState,
        onlocationchanged: null,
        file: function () {
            return {
                read: function () { return Promise.resolve(""); }
            };
        },
        event_target: window
    };
})();
