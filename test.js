hi = (function () {
  try {
    for (i in document.getElementsByClassName(
      "pv-contact-info__contact-type"
    )) {
      let el = document.getElementsByClassName("pv-contact-info__contact-type")[
        i
      ];
      if (el.className.includes("ci-email")) {
        return el.children[2].children[0].innerText;
      }
    }
  } catch (e) {
    return "";
  }
})();
