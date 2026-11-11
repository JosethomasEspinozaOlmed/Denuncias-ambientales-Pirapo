(function () {
  const lat = document.getElementById("id_latitud");
  const lon = document.getElementById("id_longitud");
  const feedback = document.getElementById("ubicacion-feedback");
  const gps = document.getElementById("usar-gps");
  const clear = document.getElementById("quitar-punto");
  if (!lat || !lon) return;
  let mapa = null;
  let marker = null;
  // Coordenadas aproximadas de Pirapó, solo para centrar el mapa (no se envían como denuncia).
  if (window.L) {
    mapa = L.map("mapa").setView([-26.85751, -55.54384], 12);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    referrerPolicy: "strict-origin-when-cross-origin"
  }).addTo(mapa);

  } else {
    document.getElementById("mapa").textContent = "El mapa no está disponible. Podés indicar tu dirección manualmente.";
  }
  function setPoint(a, b) {
    lat.value = Number(a).toFixed(6);
    lon.value = Number(b).toFixed(6);
    feedback.textContent = "Punto seleccionado: " + lat.value + ", " + lon.value;
    if (mapa) {
      if (marker) mapa.removeLayer(marker);
      marker = L.marker([a, b]).addTo(mapa);
      mapa.setView([a, b], 15);
    }
  }
  if (mapa) {
    mapa.on("click", (event) => setPoint(event.latlng.lat, event.latlng.lng));
    if (lat.value && lon.value) setPoint(lat.value, lon.value);
  }
  gps.addEventListener("click", () => {
    if (!navigator.geolocation) { feedback.textContent = "Este navegador no admite GPS. Escribí una dirección."; return; }
    navigator.geolocation.getCurrentPosition(
      (pos) => setPoint(pos.coords.latitude, pos.coords.longitude),
      () => { feedback.textContent = "No fue posible obtener el GPS. Escribí una dirección o marcá el mapa."; },
      {enableHighAccuracy:true,timeout:10000}
    );
  });
  clear.addEventListener("click", () => {
    lat.value = ""; lon.value = "";
    if (mapa && marker) {mapa.removeLayer(marker); marker = null;}
    feedback.textContent = "Punto retirado. Ingresá una dirección para registrar la denuncia.";
  });
})();
