// Mobile drawer menu shared by every page.
function toggleMenu(force) {
  const menu = document.querySelector("#mobileMenu");
  const button = document.querySelector("#menuButton");
  const open =
    typeof force === "boolean" ? force : !menu.classList.contains("open");
  menu.classList.toggle("open", open);
  menu.setAttribute("aria-hidden", String(!open));
  button.setAttribute("aria-expanded", String(open));
  document.body.classList.toggle("menu-open", open);
  if (open) {
    requestAnimationFrame(() =>
      document.querySelector("#closeMenu").focus(),
    );
  } else {
    button.focus();
  }
}
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    document.querySelector("#mobileMenu").classList.contains("open")
  )
    toggleMenu(false);
});
