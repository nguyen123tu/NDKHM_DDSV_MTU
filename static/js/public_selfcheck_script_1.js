(function() {
    const _f = window.fetch;
    window.fetch = function(u, o) {
        let isLocal = true;
        try {
            const urlStr = (typeof u === 'string') ? u : (u && u.url ? u.url : String(u));
            if (urlStr.startsWith('http://') || urlStr.startsWith('https://')) {
                if (new URL(urlStr).origin !== window.location.origin) isLocal = false;
            }
        } catch(e) {}
        
        if (isLocal) {
            let newO = o ? { ...o } : {};
            let newH = newO.headers ? newO.headers : {};
            if (newH instanceof Headers) {
                const h = new Headers(newH);
                h.set('ngrok-skip-browser-warning', '1');
                newO.headers = h;
            } else {
                newO.headers = { ...newH, 'ngrok-skip-browser-warning': '1' };
            }
            return _f.call(this, u, newO);
        }
        
        if (o === undefined) return _f.call(this, u);
        return _f.call(this, u, o);
    };
})();