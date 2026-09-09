(function () {
  function getFrame() {
    return document.getElementById("publications-frame");
  }

  window.addEventListener("message", function (event) {
    if (event.origin !== "https://gamzeh-code.github.io") return;
    if (!event.data || event.data.type !== "publications-height") return;

    var frame = getFrame();
    if (!frame) return;

    var h = Number(event.data.height);
    if (!Number.isFinite(h) || h < 300) return;

    frame.style.height = Math.ceil(h + 8) + "px";
  });
})();
