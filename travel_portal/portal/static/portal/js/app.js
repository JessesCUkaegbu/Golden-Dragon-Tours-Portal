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

    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("mainContent");
    const closeBtn = document.getElementById("sidebarToggle");
    const openBtn = document.getElementById("sidebarOpenBtn");
    const overlay = document.getElementById("sidebarOverlay");

    function openSidebar() {
        sidebar.classList.remove("collapsed");
        sidebar.classList.add("open");
        if (overlay) overlay.classList.add("active");
        if (window.innerWidth >= 993 && mainContent) {
            mainContent.classList.remove("expanded");
        }
    }

    function closeSidebar() {
        sidebar.classList.add("collapsed");
        sidebar.classList.remove("open");
        if (overlay) overlay.classList.remove("active");
        if (window.innerWidth >= 993 && mainContent) {
            mainContent.classList.add("expanded");
        }
    }

    // Open button (hamburger in topbar)
    if (openBtn) openBtn.addEventListener("click", openSidebar);

    // Close button (X inside sidebar)
    if (closeBtn) closeBtn.addEventListener("click", closeSidebar);

    // Clicking overlay closes sidebar on mobile
    if (overlay) overlay.addEventListener("click", closeSidebar);

});