"""Pruebas de la política de expiración (no requieren MongoDB ni Redis)."""
import unittest

from cache import ttl_para

DESC_CORTA = "Va sobre rieles"  # 15 caracteres


class TtlParaTest(unittest.TestCase):
    def test_identificador_de_5_o_menos_caracteres_15s(self):
        self.assertEqual(ttl_para("Tren", DESC_CORTA), 15)
        self.assertEqual(ttl_para("Barco", DESC_CORTA), 15)  # 5 exactos

    def test_identificador_de_6_a_10_caracteres_20s(self):
        self.assertEqual(ttl_para("Lancha", DESC_CORTA), 20)  # 6
        self.assertEqual(ttl_para("Automóvil", DESC_CORTA), 20)  # 9 (la tilde cuenta 1)
        self.assertEqual(ttl_para("Patineta12", DESC_CORTA), 20)  # 10 exactos

    def test_identificador_de_mas_de_10_caracteres_40s(self):
        self.assertEqual(ttl_para("Patineta123", DESC_CORTA), 40)  # 11
        self.assertEqual(ttl_para("Helicóptero", DESC_CORTA), 40)  # 11
        self.assertEqual(ttl_para("Transbordador", DESC_CORTA), 40)  # 13

    def test_descripcion_de_mas_de_20_caracteres_no_se_cachea(self):
        self.assertIsNone(ttl_para("Tren", "x" * 21))

    def test_descripcion_de_exactamente_20_caracteres_si_se_cachea(self):
        self.assertEqual(ttl_para("Tren", "x" * 20), 15)

    def test_la_descripcion_tiene_prioridad_sobre_el_identificador(self):
        self.assertIsNone(ttl_para("Transbordador", "x" * 21))


if __name__ == "__main__":
    unittest.main()
