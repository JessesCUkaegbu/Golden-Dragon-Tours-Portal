document.addEventListener("DOMContentLoaded", function () {

    // ── Auto-dismiss alerts ──────────────────────────────
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = "0.4s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-8px)";
            setTimeout(() => alert.remove(), 400);
        }, 3000);
    });

    // ── Sidebar overlay close on mobile ─────────────────
    document.addEventListener("click", function (e) {
        const sidebar = document.getElementById("sidebar");
        const toggle = document.getElementById("sidebarToggle");
        if (
            sidebar &&
            sidebar.classList.contains("open") &&
            !sidebar.contains(e.target) &&
            toggle &&
            !toggle.contains(e.target)
        ) {
            sidebar.classList.remove("open");
        }
    });

    // ── Active nav link highlight ────────────────────────
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".sidebar-nav a");
    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            navLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");
        }
    });