/* Formulario de ubicación y previsualización. No sustituye validación de Django. */
(function () {
  "use strict";
  const lat = document.getElementById("id_latitud");
  const lon = document.getElementById("id_longitud");
  const direccion = document.getElementById("id_direccion");
  const feedback = document.getElementById("ubicacion-feedback");
  const gps = document.getElementById("usar-gps");
  const quitar = document.getElementById("quitar-punto");
  const mapContainer = document.getElementById("mapa");
  const form = document.getElementById("form-denuncia");
  const file = document.getElementById("id_foto");
  const fileName = document.getElementById("foto-nombre");
  const preview = document.getElementById("foto-vista-previa");
  if (!lat || !lon || !mapContainer || !feedback) return;

  let mapa = null;
  let marcador = null;
  let imageUrl = null;
  // Centro aproximado de Pirapó: NO se registra como ubicación de la denuncia.
  if (window.L) {
    mapa = window.L.map(mapContainer).setView([-26.85751, -55.54384], 12);
    window.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      referrerPolicy: "strict-origin-when-cross-origin"
    }).addTo(mapa);
  } else {
    mapContainer.classList.add("map-fallback");
    mapContainer.textContent = "El mapa no está disponible. Podés indicar la dirección del problema manualmente.";
  }

  function indicarPunto(a, b) {
    lat.value = Number(a).toFixed(6);
    lon.value = Number(b).toFixed(6);
    feedback.textContent = "Punto seleccionado: " + lat.value + ", " + lon.value;
    feedback.classList.add("point-selected");
    if (mapa) {
      if (marcador) mapa.removeLayer(marcador);
      marcador = window.L.marker([a, b]).addTo(mapa);
      mapa.setView([a, b], 15);
    }
  }

  if (mapa) {
    mapa.on("click", (evento) => indicarPunto(evento.latlng.lat, evento.latlng.lng));
    if (lat.value && lon.value) indicarPunto(lat.value, lon.value);
  }
  if (gps) gps.addEventListener("click", () => {
    if (!navigator.geolocation) {
      feedback.textContent = "Tu navegador no permite acceder al GPS. Indicá la dirección manualmente.";
      return;
    }
    gps.disabled = true;
    feedback.textContent = "Buscando ubicación del dispositivo...";
    navigator.geolocation.getCurrentPosition(
      (pos) => { gps.disabled = false; indicarPunto(pos.coords.latitude, pos.coords.longitude); },
      () => { gps.disabled = false; feedback.textContent = "No fue posible obtener el GPS. Indicá una dirección o marcá el mapa."; },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  });
  if (quitar) quitar.addEventListener("click", () => {
    lat.value = "";
    lon.value = "";
    if (mapa && marcador) { mapa.removeLayer(marcador); marcador = null; }
    feedback.textContent = "Punto retirado. Ingresá una dirección o seleccioná otro punto.";
    feedback.classList.remove("point-selected");
  });
  if (form) form.addEventListener("submit", (evento) => {
    // Ayuda inmediata: la validación definitiva también se ejecuta en Django.
    if (direccion && !direccion.value.trim() && !(lat.value && lon.value)) {
      evento.preventDefault();
      feedback.textContent = "Indicá al menos una dirección o seleccioná un punto en el mapa.";
      feedback.classList.remove("point-selected");
      direccion.focus();
      return;
    }
    const cat = document.getElementById("id_categoria");
    const descripcion = document.getElementById("id_descripcion");
    for (const campo of [cat, descripcion]) {
      if (campo && !campo.value.trim()) { evento.preventDefault(); campo.focus(); campo.reportValidity(); return; }
    }
  });
  if (file && fileName && preview) {
    file.addEventListener("change", () => {
      if (imageUrl) { URL.revokeObjectURL(imageUrl); imageUrl = null; }
      const archivo = file.files && file.files[0];
      if (!archivo) { preview.hidden = true; preview.removeAttribute("src"); fileName.textContent = "Ninguna fotografía seleccionada."; return; }
      fileName.textContent = "Seleccionada: " + archivo.name;
      if (!archivo.type.startsWith("image/")) { preview.hidden = true; return; }
      imageUrl = URL.createObjectURL(archivo);
      preview.src = imageUrl;
      preview.hidden = false;
    });
  }
})();
