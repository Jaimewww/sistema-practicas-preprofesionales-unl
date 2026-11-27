/* Mascota UNL animada: ciclo automatico, hover/focus y click con globo. */
(function () {
  'use strict';
  var ACCIONES = ['saludar', 'saltar', 'balancear'];
  var DURACION = { saludar: 1800, saltar: 700, balancear: 1600 };
  var GLOBO_MS = 3500;

  function reducido() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function primerNombre() {
    var el = document.querySelector('.usermenu .uname');
    if (!el) return '';
    var txt = '';
    for (var i = 0; i < el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType === 3) txt += el.childNodes[i].nodeValue;
    }
    txt = txt.replace(/^\s+|\s+$/g, '');
    return txt ? txt.split(/\s+/)[0] : '';
  }

  function iniciar(oso) {
    var activa = null, tAccion = 0, tGlobo = 0, globo = null, indice = 0, mensaje = 0;

    function parar() {
      if (activa) oso.classList.remove('oso--' + activa);
      activa = null;
      clearTimeout(tAccion);
    }
    function hacer(nombre) {
      if (reducido()) return;
      parar();
      activa = nombre;
      // reflow para reiniciar la animacion
      void oso.offsetWidth;
      oso.classList.add('oso--' + nombre);
      tAccion = setTimeout(function () {
        oso.classList.remove('oso--' + nombre);
        activa = null;
      }, DURACION[nombre]);
    }
    function libre() { return !activa; }

    function mensajes() {
      var n = primerNombre();
      return ['¡Hola' + (n ? ', ' + n : '') + '!', '¡Bienvenido al SIAAF!', '¡Qué gusto verte!'];
    }
    function mostrarGlobo() {
      var lista = mensajes();
      if (!globo) {
        globo = document.createElement('p');
        globo.className = 'oso__globo';
        globo.setAttribute('role', 'status');
        oso.appendChild(globo);
      }
      globo.textContent = lista[mensaje % lista.length];
      mensaje++;
      clearTimeout(tGlobo);
      tGlobo = setTimeout(function () {
        if (globo && globo.parentNode) globo.parentNode.removeChild(globo);
        globo = null;
      }, GLOBO_MS);
    }

    oso.addEventListener('click', function () {
      mostrarGlobo();
      hacer('saludar');
    });

    if (reducido()) return;

    function alEntrar() {
      if (!libre()) return;
      hacer('saltar');
      setTimeout(function () { if (libre()) hacer('saludar'); }, DURACION.saltar + 20);
    }
    oso.addEventListener('mouseenter', alEntrar);
    oso.addEventListener('focus', alEntrar);

    function ciclo() {
      if (libre()) {
        hacer(ACCIONES[indice % ACCIONES.length]);
        indice++;
      }
    }
    setTimeout(function () {
      ciclo();
      setInterval(ciclo, 7000);
    }, 1500);
  }

  function arrancar() {
    var osos = document.querySelectorAll('.oso');
    for (var i = 0; i < osos.length; i++) iniciar(osos[i]);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', arrancar);
  else arrancar();
})();
