import numpy as np

# Parámetros del extremófilo y vinaza
mu_max = 0.8       # Tasa máxima (1/día)
Ks = 2.5           # Constante saturación DQO (g/L)
Y_XS = 0.45        # Rendimiento biomasa/vinaza

# Rangos de temperatura (°C)
T_opt = 45.0
T_min = 15.0
T_max = 60.0

def factor_temperatura(T):
    """Modelo térmico de Ratkowsky"""
    if T <= T_min or T >= T_max:
        return 0.0
    num = (T - T_max) * ((T - T_min) ** 2)
    den = (T_opt - T_min) * ((T_opt - T_min)*(T - T_opt) - (T_opt - T_max)*(T_opt + T_min - 2*T))
    return max(0.0, num / den)

def calcular_tasas(biomasa, dqo, temp):
    """Calcula la velocidad de crecimiento y de limpieza"""
    if dqo <= 0:
        return 0.0, 0.0
    
    f_T = factor_temperatura(temp)
    mu = mu_max * (dqo / (Ks + dqo)) * f_T
    
    crecimiento_biomasa = mu * biomasa
    limpieza_vinaza = -(1 / Y_XS) * mu * biomasa
    
    return crecimiento_biomasa, limpieza_vinaza