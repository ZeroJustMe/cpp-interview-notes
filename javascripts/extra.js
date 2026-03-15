// 阅读进度条
document.addEventListener("DOMContentLoaded", function () {
  // 创建进度条元素
  var bar = document.createElement("div");
  bar.id = "progress-bar";
  document.body.prepend(bar);

  // 更新进度条
  function updateProgress() {
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (docHeight > 0) {
      var progress = (scrollTop / docHeight) * 100;
      bar.style.width = Math.min(progress, 100) + "%";
    }
  }

  window.addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();

  // MkDocs Material instant navigation 兼容：页面切换后重置
  if (typeof document$ !== "undefined") {
    document$.subscribe(function () {
      updateProgress();
    });
  }
});
