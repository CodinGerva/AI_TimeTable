// Example of using AJAX to load data into the main content area
function loadSection(section) {
  fetch(`/get_${section}`)
    .then((response) => response.text())
    .then((html) => {
      document.querySelector('main').innerHTML = html
    })
}

document.querySelectorAll('.nav-link').forEach((link) => {
  link.addEventListener('click', function () {
    loadSection(this.text.trim().toLowerCase())
  })
})
