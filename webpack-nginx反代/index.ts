export { };

declare global {
    interface Window {
        __proxy_hook_injected__?: boolean;
    }
}

(function () {
    if (window.__proxy_hook_injected__) return; window.__proxy_hook_injected__ = true;

    const d = ["i0.hdslb.com", "i1.hdslb.com", "static.hdslb.com", "s0.hdslb.com", "i2.hdslb.com", "s1.hdslb.com", "s2.hdslb.com", "pic.bilibili.com"];
    const h = ["bilibili.com", "www.bilibili.com"];
    const p = "https://bilibili.atomglimpses.cn/proxy_bili/";
    const main_p = "https://bilibili.atomglimpses.cn";

    function r(u: string | undefined): string {
        if (!u || typeof u !== "string") return u as any;
        for (const x of h) {
            const hp = ["https://" + x, "http://" + x, "//" + x];
            for (const pre of hp) {
                if (u.startsWith(pre)) {
                    return u.replace(pre, pre.startsWith("//") ? main_p.replace("https:", "") : main_p);
                }
            }
        }
        for (const x of d) {
            const hp = ["https://" + x, "http://" + x, "//" + x];
            for (const pre of hp) {
                if (u.startsWith(pre)) {
                    return u.replace(pre, pre.startsWith("//") ? p.replace("https:", "") + x : p + x);
                }
            }
        }
        return u;
    }

    function rewriteSrcset(s: string | undefined): string {
        if (!s || typeof s !== "string") return s as any;
        return s.split(",").map(e => {
            const a = e.trim().split(/\s+/);
            if (a[0]) a[0] = r(a[0]);
            return a.join(" ");
        }).join(", ");
    }

    const xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (m: string, u: string | URL, ...args: any[]) {
        try { u = u instanceof URL ? u.href : u; u = r(u); } catch (e) { }
        return xo.apply(this, [m, u, ...args] as any);
    };

    const fo = window.fetch;
    window.fetch = function (i, n) {
        try {
            if (typeof i === "string") i = r(i);
            else if (i instanceof Request) i = new Request(r(i.url), i);
        } catch (e) { }
        return fo(i, n);
    };

    function rewriteElementAttributes(el: Element): void {
        if (el.hasAttribute("src")) el.setAttribute("src", r((el as any).src));
        if (el.hasAttribute("href")) el.setAttribute("href", r((el as any).href));
        if (el.hasAttribute("srcset")) el.setAttribute("srcset", rewriteSrcset((el as any).srcset));
    }

    function rewriteExisting() {
        document.querySelectorAll("img,script,link,video,source,a").forEach(rewriteElementAttributes);
    }

    function observeDOM() {
        const ob = new MutationObserver(ms => {
            for (const m of ms) {
                for (const n of Array.from(m.addedNodes)) {
                    if (n.nodeType === 1) {
                        rewriteElementAttributes(n as Element);
                        if (n instanceof Element && n.querySelectorAll)
                            n.querySelectorAll("img,script,link,video,source,a").forEach(rewriteElementAttributes);
                    }
                }
            }
        });
        ob.observe(document.documentElement, { childList: true, subtree: true });
    }

    function init() {
        rewriteExisting();
        observeDOM();
        console.log("[proxy_hook5] active");
    }

    if (document.readyState === "loading") {
        window.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    ["pushState", "replaceState"].forEach((fn: string) => {
        const orig = (history as any)[fn];
        (history as any)[fn] = function () {
            const res = orig.apply(this, arguments);
            setTimeout(rewriteExisting, 500);
            return res;
        };
    });

    setInterval(() => {
        try {
            const scripts = [...document.scripts];
            const alive = scripts.some(s => s.src && s.src.includes("proxy_hook"));
            if (!alive) {
                console.warn("[proxy_hook5] script lost, reinjecting...");
                const newScript = document.createElement("script");
                newScript.src = "https://safe.atomglimpses.cn/proxy_hook5.js?ts=" + Date.now();
                newScript.async = true;
                document.documentElement.appendChild(newScript);
            }
        } catch (e) {
            console.error("[proxy_hook5] watchdog error:", e);
        }
    }, 5000);

})();