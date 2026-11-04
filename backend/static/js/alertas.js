// API enhancement for synthetic notifications and coordinator screens.
// Native forms and <details> keep the server-rendered alternative usable.
(function () {
  'use strict';
  var body = document.body;
  var rol = body.dataset.rolDemo;
  if (!rol || !window.fetch) return;
  var lista = document.querySelector('[data-alertas-lista]');
  var filtros = document.querySelector('[data-alertas-filtros]');

  function element(tag, text, className) {
    var node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function count(value) {
    document.querySelectorAll('[data-alertas-count]').forEach(function (node) {
      node.textContent = String(value);
    });
  }

  function error(selector, message) {
    var node = document.querySelector(selector);
    if (node) {
      node.textContent = message;
      node.hidden = !message;
    }
  }

  function notifications(alertas) {
    var ul = document.querySelector('[data-notificaciones-lista]');
    ul.replaceChildren();
    alertas.forEach(function (alerta) {
      var li = element('li');
      var link = element('a', alerta.tipo_display + ' · ' + alerta.practica.estudiante);
      link.href = alerta.practica.detalle_url;
      li.append(link, element('p', alerta.detalle));
      ul.append(li);
    });
    if (!alertas.length) ul.append(element('li', 'No hay alertas activas.'));
  }

  function table(alertas) {
    if (!lista) return;
    var tbody = lista.querySelector('[data-alertas-filas]');
    tbody.replaceChildren();
    alertas.forEach(function (alerta) {
      var row = element('tr');
      var tipo = element('td');
      tipo.dataset.label = 'Tipo';
      var colors = { fuera_de_plazo: 'bad', por_confirmar: 'warn', rezagada: 'bad' };
      tipo.append(element('span', alerta.tipo_display, 'badge badge--' + (colors[alerta.estado_badge] || 'neutral')));
      var practica = element('td');
      practica.dataset.label = 'Práctica';
      practica.append(element('strong', alerta.practica.estudiante), element('br'), element('span', alerta.practica.tipo_display, 'cell-line'));
      var detalle = element('td', alerta.detalle);
      detalle.dataset.label = 'Detalle';
      var fecha = element('td', alerta.fecha.split('-').reverse().join('/'));
      fecha.dataset.label = 'Desde';
      var accion = element('td', undefined, 'data-table__action');
      accion.dataset.label = 'Acción';
      var link = element('a', 'Ver práctica', 'link-action');
      link.href = alerta.practica.detalle_url;
      link.append(element('span', ' de ' + alerta.practica.estudiante, 'sr-only'));
      accion.append(link);
      row.append(tipo, practica, detalle, fecha, accion);
      tbody.append(row);
    });
    lista.querySelector('[data-alertas-tabla]').hidden = !alertas.length;
    lista.querySelector('[data-alertas-vacio]').hidden = !!alertas.length;
    lista.querySelector('[data-alertas-visible]').textContent = alertas.length + (alertas.length === 1 ? ' alerta' : ' alertas');
  }

  async function read(tipo) {
    var url = new URL(body.dataset.alertasUrl, window.location.origin);
    if (tipo) url.searchParams.set('tipo', tipo);
    try {
      var response = await fetch(url, { headers: { 'X-Rol': rol }, credentials: 'same-origin' });
      if (!response.ok) throw new Error();
      var payload = await response.json();
      count(payload.count);
      return payload;
    } catch (_) {
      throw new Error('No se pudieron actualizar las alertas. Se conserva la última consulta.');
    }
  }

  var inicial = read('').then(function (payload) {
    notifications(payload.alertas);
    if (lista) {
      var tipo = lista.dataset.alertasTipo;
      table(payload.alertas.filter(function (alerta) { return !tipo || alerta.tipo === tipo; }));
    }
  }).catch(function (failure) {
    error('[data-alertas-error]', failure.message);
    error('[data-alertas-lista-error]', failure.message);
  });

  if (filtros) filtros.addEventListener('submit', async function (event) {
    event.preventDefault();
    var button = filtros.querySelector('button[type="submit"]');
    button.disabled = true;
    // Finish the initial request first so it cannot overwrite a later filter.
    await inicial;
    try {
      var tipo = filtros.elements.tipo.value;
      var payload = await read(tipo);
      table(payload.alertas);
      error('[data-alertas-lista-error]', '');
      var url = new URL(window.location.href);
      if (tipo) url.searchParams.set('tipo', tipo);
      else url.searchParams.delete('tipo');
      window.history.replaceState(null, '', url);
    } catch (failure) {
      error('[data-alertas-lista-error]', failure.message);
    } finally {
      button.disabled = false;
    }
  });

  var form = document.querySelector('[data-cierre-api]');
  if (form) form.addEventListener('submit', async function (event) {
    event.preventDefault();
    var panel = form.querySelector('[data-cierre-error]');
    var mensaje = form.querySelector('[data-cierre-mensaje]');
    var faltantes = form.querySelector('[data-cierre-faltante]');
    var button = form.querySelector('button[type="submit"]');
    panel.hidden = true;
    faltantes.replaceChildren();
    if (!form.elements.confirmar.checked) {
      mensaje.textContent = 'Confirme el cierre de la práctica antes de continuar.';
      panel.hidden = false;
      panel.focus();
      return;
    }
    button.disabled = true;
    try {
      var response = await fetch(form.dataset.cierreApi, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'X-Rol': rol, 'X-CSRFToken': form.elements.csrfmiddlewaretoken.value }
      });
      var payload;
      try { payload = await response.json(); }
      catch (_) { throw new Error('No se pudo confirmar el cierre. Recargue la página para consultar el estado.'); }
      if (!response.ok) {
        mensaje.textContent = payload.error.message;
        (payload.error.faltante || []).forEach(function (item) { faltantes.append(element('li', item)); });
        panel.hidden = false;
        panel.focus();
        return;
      }
      window.location.assign(form.dataset.cierreDestino);
    } catch (failure) {
      mensaje.textContent = failure instanceof TypeError
        ? 'No se pudo conectar para confirmar el cierre. Recargue la página para consultar el estado.'
        : failure.message;
      panel.hidden = false;
      panel.focus();
    } finally {
      button.disabled = false;
    }
  });
})();
