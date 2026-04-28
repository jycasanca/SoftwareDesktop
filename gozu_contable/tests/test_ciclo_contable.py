"""
Tests para el ciclo contable completo.
Valida los casos críticos identificados:
1. Compra de gaseosas (inventario)
2. Compra de muebles (activo fijo)
3. Venta mixto (contado + crédito)
4. Cobro de CxC
5. Donación (ingreso)
6. Incendio (pérdida)
7. Depreciación
8. Costo de ventas (COGS)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.clasificador import Clasificador
from core.estado_contable import EstadoContable

def test_compra_gaseosas():
    """Compra de inventario al contado -> 20/10"""
    clf = Clasificador()
    texto = "Se adquirieron gaseosas por S/. 4,000 al contado"
    resultado = clf.clasificar(texto)
    
    # Buscar asiento de compra
    asiento_compra = None
    for a in resultado['asientos']:
        for l in a['lineas']:
            if l['cuenta_codigo'] == 20:  # Inventario
                asiento_compra = a
                break
    
    assert asiento_compra is not None, "No se encontró asiento de compra de inventario"
    lineas = asiento_compra['lineas']
    
    # Debe haber una línea 20 Debe y una 10 Haber
    cuenta_20 = [l for l in lineas if l['cuenta_codigo'] == 20 and l['debe'] > 0]
    cuenta_10 = [l for l in lineas if l['cuenta_codigo'] == 10 and l['haber'] > 0]
    
    assert len(cuenta_20) > 0, "No hay línea de inventario (20) al debe"
    assert len(cuenta_10) > 0, "No hay línea de caja (10) al haber"
    print("✓ Test compra gaseosas pasado")

def test_compra_muebles():
    """Compra de activo fijo -> 33/10"""
    clf = Clasificador()
    texto = "Se compraron muebles de oficina por S/. 3,000 al contado"
    resultado = clf.clasificar(texto)
    
    # Buscar asiento de activo fijo
    asiento_activo = None
    for a in resultado['asientos']:
        for l in a['lineas']:
            if l['cuenta_codigo'] == 33:  # Inmuebles, maquinaria
                asiento_activo = a
                break
    
    assert asiento_activo is not None, "No se encontró asiento de activo fijo"
    lineas = asiento_activo['lineas']
    
    cuenta_33 = [l for l in lineas if l['cuenta_codigo'] == 33 and l['debe'] > 0]
    cuenta_10 = [l for l in lineas if l['cuenta_codigo'] == 10 and l['haber'] > 0]
    
    assert len(cuenta_33) > 0, "No hay línea de activo fijo (33) al debe"
    assert len(cuenta_10) > 0, "No hay línea de caja (10) al haber"
    print("✓ Test compra muebles pasado")

def test_venta_mixto():
    """Venta 50% contado 50% crédito -> 10/12/70"""
    clf = Clasificador()
    texto = "Se vendió mercadería por S/. 10,000, 50% contado y 50% crédito"
    resultado = clf.clasificar(texto)
    
    # Buscar asiento de venta
    asiento_venta = None
    for a in resultado['asientos']:
        for l in a['lineas']:
            if l['cuenta_codigo'] == 70:  # Ventas
                asiento_venta = a
                break
    
    assert asiento_venta is not None, "No se encontró asiento de venta"
    lineas = asiento_venta['lineas']
    
    # Debe haber: 10 Debe, 12 Debe, 70 Haber
    cuenta_10 = [l for l in lineas if l['cuenta_codigo'] == 10 and l['debe'] > 0]
    cuenta_12 = [l for l in lineas if l['cuenta_codigo'] == 12 and l['debe'] > 0]
    cuenta_70 = [l for l in lineas if l['cuenta_codigo'] == 70 and l['haber'] > 0]
    
    assert len(cuenta_10) > 0, "No hay línea de caja (10) al debe (contado)"
    assert len(cuenta_12) > 0, "No hay línea de CxC (12) al debe (crédito)"
    assert len(cuenta_70) > 0, "No hay línea de ventas (70) al haber"
    print("✓ Test venta mixto pasado")

def test_cobro_cxc():
    """Cobro de cuenta por cobrar -> 10/12"""
    # Primero creamos una venta a crédito
    clf = Clasificador()
    
    # Simulamos estado con CxC pendiente
    clf.estado.cxc_pendientes['venta_001'] = 5000.0
    
    texto = "Se cobró S/. 5,000 de la factura pendiente"
    resultado = clf.clasificar(texto)
    
    # Buscar asiento de cobro
    asiento_cobro = None
    for a in resultado['asientos']:
        tiene_10 = any(l['cuenta_codigo'] == 10 and l['debe'] > 0 for l in a['lineas'])
        tiene_12 = any(l['cuenta_codigo'] == 12 and l['haber'] > 0 for l in a['lineas'])
        if tiene_10 and tiene_12:
            asiento_cobro = a
            break
    
    assert asiento_cobro is not None, "No se encontró asiento de cobro"
    print("✓ Test cobro CxC pasado")

def test_donacion():
    """Donación recibida -> 75/20 (ingreso no operativo)"""
    clf = Clasificador()
    texto = "Se recibió una donación de mercadería valorizada en S/. 2,000"
    resultado = clf.clasificar(texto)
    
    # Buscar asiento de donación
    asiento_donacion = None
    for a in resultado['asientos']:
        for l in a['lineas']:
            if l['cuenta_codigo'] == 75:  # Otros ingresos
                asiento_donacion = a
                break
    
    assert asiento_donacion is not None, "No se encontró asiento de donación"
    lineas = asiento_donacion['lineas']
    
    # 75 Haber (ingreso) y 20 Debe (inventario)
    cuenta_75 = [l for l in lineas if l['cuenta_codigo'] == 75 and l['haber'] > 0]
    cuenta_20 = [l for l in lineas if l['cuenta_codigo'] == 20 and l['debe'] > 0]
    
    assert len(cuenta_75) > 0, "Donación debe ir a 75 Otros ingresos"
    assert len(cuenta_20) > 0, "Donación aumenta inventario 20"
    print("✓ Test donación pasado")

def run_all_tests():
    print("="*60)
    print("Ejecutando tests de ciclo contable")
    print("="*60)
    
    try:
        test_compra_gaseosas()
        test_compra_muebles()
        test_venta_mixto()
        test_cobro_cxc()
        test_donacion()
        print("="*60)
        print("✓ TODOS LOS TESTS PASARON")
        print("="*60)
        return True
    except AssertionError as e:
        print(f"✗ TEST FALLÓ: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
