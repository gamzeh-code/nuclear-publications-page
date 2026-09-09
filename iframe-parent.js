(function () {
  var lastHeight = -1;

  window.addEventListener("message", function (event) {
    if (event.origin !== "https://gamzeh-code.github.io") return;
    if (!event.data || event.data.type !== "publications-height") return;

    var frame = document.getElementById("publications-frame");
    if (!frame) return;

    var h = Math.ceil(Number(event.data.height));
    if (!Number.isFinite(h) || h < 300) return;
    if (Math.abs(h - lastHeight) < 2) return;

    lastHeight = h;
    frame.style.setProperty("height", h + "px", "important");
  });
})();
