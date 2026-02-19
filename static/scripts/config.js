(() => {
    const host = window.location.hostname || "127.0.0.1";
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    const defaultBaseUrl = `${protocol}//${host}:5001`;
    const configuredBaseUrl = window.APP_CONFIG?.BASE_URL;

    window.APP_CONFIG = window.APP_CONFIG || {};
    window.APP_CONFIG.BASE_URL = configuredBaseUrl || defaultBaseUrl;
})();
