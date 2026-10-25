"""N1 (catálogo de entidades) y N2 (convenios) del issue #55.

Las dos pantallas son de consulta: catálogo y convenios no ofrecen ninguna
acción de edición ni de firma (spec §4, «Fuera del alcance»).
"""
from copy import deepcopy

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from . import entidad as catalogo
from . import sample_data as data

ENTIDADES_DEL_CATALOGO = (
    "Universidad Nacional de Loja - Carrera de Computación",
    "Junta Parroquial de San Lucas",
    "Soluciones Informáticas del Sur Cía. Ltda.",
    "Agroindustrias del Norte Cía. Ltda.",
    "GAD Parroquial de Vilcabamba",
    "GAD Municipal de Catamayo",
)


@override_settings(DEBUG=True)
class CatalogoEntidadesTests(SimpleTestCase):
    def url(self, name, *args):
        return reverse(f"prototipo:{name}", args=args)

    # --- N1 catálogo (lista) ----------------------------------------------

    def test_n1_lista_las_entidades_con_instrumento_y_vigencia(self):
        response = self.client.get(self.url("catalogo_entidades"))
        self.assertEqual(response.status_code, 200)
        nombres = [item["entidad"]["nombre"] for item in response.context["entidades"]]
        self.assertEqual(sorted(nombres), sorted(ENTIDADES_DEL_CATALOGO))
        self.assertContains(response, "Convenio")
        self.assertContains(response, "Carta de compromiso")
        # Vigencia resuelta contra HOY (2026-06-05): una vencida y el resto vigentes.
        self.assertContains(response, "Vencido")
        self.assertContains(response, "Vigente")

    def test_n1_lista_marca_la_entidad_sin_practicas_vigentes(self):
        response = self.client.get(self.url("catalogo_entidades"))
        self.assertContains(response, "Sin prácticas vigentes")
        items = {item["entidad"]["nombre"]: item for item in response.context["entidades"]}
        self.assertEqual(items["GAD Municipal de Catamayo"]["practicas_vigentes"], [])
        self.assertTrue(items["Soluciones Informáticas del Sur Cía. Ltda."]["practicas_vigentes"])

    def test_n1_vistas_usan_el_menu_de_entidad(self):
        for name, args in (
            ("catalogo_entidades", ()),
            ("detalle_entidad", (1,)),
            ("convenios", ()),
        ):
            with self.subTest(name=name):
                response = self.client.get(self.url(name, *args))
                self.assertContains(response, 'href="/prototipo/entidad/catalogo/"')
                self.assertContains(response, 'href="/prototipo/entidad/convenios/"')

    # --- N1 detalle (solo lectura, HU-07) ---------------------------------

    def test_n1_detalle_muestra_las_practicas_vigentes_de_la_entidad(self):
        response = self.client.get(self.url("detalle_entidad", 1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entidad"]["nombre"], ENTIDADES_DEL_CATALOGO[0])
        self.assertContains(response, "MENDIETA SARANGO LUCIANA BELÉN")
        self.assertContains(response, "JIMÉNEZ CASTILLO DIEGO ALEJANDRO")

    def test_n1_detalle_sin_practicas_vigentes_muestra_el_vacio(self):
        response = self.client.get(self.url("detalle_entidad", 6))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Esta entidad no tiene prácticas vigentes")
        # Su única práctica está cerrada (id 9), así que no se lista.
        self.assertNotContains(response, "AYOVI CANDO MARIA FERNANDA")

    def test_n1_detalle_desconocido_devuelve_404(self):
        self.assertEqual(self.client.get(self.url("detalle_entidad", 99999)).status_code, 404)

    def test_n1_detalle_es_solo_lectura(self):
        response = self.client.get(self.url("detalle_entidad", 1))
        self.assertNotContains(response, "<form")
        self.assertNotContains(response, "Guardar")
        self.assertNotContains(response, "Registrar")

    # --- N2 convenios ------------------------------------------------------

    def test_n2_etiqueta_cada_convenio_fuera_del_mvp(self):
        response = self.client.get(self.url("convenios"))
        self.assertEqual(response.status_code, 200)
        convenios = response.context["convenios"]
        self.assertEqual(len(convenios), len(ENTIDADES_DEL_CATALOGO))
        # Un aviso de la pantalla y una etiqueta por cada elemento de la lista.
        etiqueta = "Fuera del MVP — proyecto R"
        self.assertEqual(response.content.decode().count(etiqueta), len(convenios) + 1)

    def test_n2_muestra_vigencia_y_estado_de_aprobacion(self):
        response = self.client.get(self.url("convenios"))
        self.assertContains(response, "Vencido")
        self.assertContains(response, "Pendiente de aprobación")
        self.assertContains(response, "Aprobado")
        self.assertContains(response, "spec §4")

    def test_n2_no_ofrece_acciones_de_firma_ni_edicion(self):
        response = self.client.get(self.url("convenios"))
        self.assertNotContains(response, "<form")
        for accion in ("Firmar", "Registrar", "Editar", "Guardar"):
            self.assertNotContains(response, accion)

    # --- Sólo GET, sólo en DEBUG -----------------------------------------

    def test_los_catalogos_solo_admiten_get(self):
        for name, args in (
            ("catalogo_entidades", ()),
            ("detalle_entidad", (1,)),
            ("convenios", ()),
        ):
            for method in ("post", "put", "delete"):
                with self.subTest(name=name, method=method):
                    response = getattr(self.client, method)(self.url(name, *args))
                    self.assertEqual(response.status_code, 405)

    @override_settings(DEBUG=False)
    def test_las_rutas_del_catalogo_son_404_sin_debug(self):
        for name, args in (
            ("catalogo_entidades", ()),
            ("detalle_entidad", (1,)),
            ("convenios", ()),
        ):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.url(name, *args)).status_code, 404)

    # --- Datos -------------------------------------------------------------

    def test_las_consultas_del_catalogo_no_mutan_sample_data(self):
        antes = deepcopy(data.practicas_de_la_carrera())
        primera = catalogo.entidades()
        primera[0]["nombre"] = "MUTADA"
        primera[0]["vigencia_hasta"] = None
        vigentes = catalogo.practicas_vigentes_de_la_entidad("GAD Parroquial de Vilcabamba")
        vigentes[0]["estado"] = "cerrada"

        self.assertNotEqual(catalogo.entidades()[0]["nombre"], "MUTADA")
        self.assertIsNotNone(catalogo.entidades()[0]["vigencia_hasta"])
        self.assertEqual(
            [(p["id"], p["estado"]) for p in antes],
            [(p["id"], p["estado"]) for p in data.practicas_de_la_carrera()],
        )
        self.assertEqual(
            [p["estado"] for p in catalogo.practicas_vigentes_de_la_entidad("GAD Parroquial de Vilcabamba")],
            ["asignada"],
        )
