// "사이트 바로가기": open the official site through go/<id>/ in a new tab. Buttons marked
// data-detail also move this tab to the service's detail page, so coming back lands there.
document.addEventListener("click", (e) => {
  const button = e.target.closest("[data-go]");
  if (!button) return;
  const root = document.body.dataset.root || "";
  window.open(`${root}go/${button.dataset.go}/`, "_blank", "noopener");
  if (button.hasAttribute("data-detail")) location.href = `${root}webhard/${button.dataset.go}/`;
});
