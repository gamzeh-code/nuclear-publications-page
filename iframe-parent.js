(function () {
  var lastHeights = {};

  var targets = {
    "publications-height": "publications-frame",
    "latest-publications-height": "latest-publications-frame"
  };

  window.addEventListener("message", function (event) {
    if (event.origin !== "https://gamzeh-code.github.io") return;
    if (!event.data || !targets[event.data.type]) return;

    var frameId = targets[event.data.type];
    var frame = document.getElementById(frameId);
    if (!frame) return;

    var h = Math.ceil(Number(event.data.height));
    if (!Number.isFinite(h) || h < 100) return;

    if (Math.abs(h - (lastHeights[frameId] || -1)) < 2) return;

    lastHeights[frameId] = h;
    frame.style.setProperty("height", h + "px", "important");
  });
})();
