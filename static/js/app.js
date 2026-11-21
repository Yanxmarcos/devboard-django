(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("devboard-theme");
  const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const applyTheme = (theme) => {
    root.setAttribute("data-bs-theme", theme);
    const icon = document.querySelector("#themeToggle i");
    if (icon) icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
  };
  applyTheme(savedTheme || preferredTheme);
  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    localStorage.setItem("devboard-theme", next);
    applyTheme(next);
  });
})();
