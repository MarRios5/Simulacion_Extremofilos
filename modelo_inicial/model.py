import numpy as np
from scipy.integrate import solve_ivp

def ecuacion_shp(t, y, fase, params):
    """
    Sistema simplificado de 2 EDOs:
    y[0] = X (Biomasa g/L)
    y[1] = S (Sustrato / DQO %)
    """
    X, S = y
    
    if fase == 'heterotrofia':
        # Fase 1: Crecimiento heterotrófico y remoción de DQO
        mu_max = params['mu_het']
        Ks = params['Ks']
        Y_xs = params['Y_xs']
        
        # Cinética de Monod
        mu = mu_max * (S / (Ks + S)) if S > 0 else 0
        
        dXdt = mu * X                  # Ganancia de biomasa
        dSdt = -(1 / Y_xs) * mu * X     # Consumo de DQO
        
    else:  # fotoinducción
        # Fase 2: Crecimiento autotrófico/mantenimiento con luz
        mu_max = params['mu_fot']
        
        dXdt = mu_max * X               # Crecimiento celular por luz
        dSdt = -0.01 * X                # Consumo residual mínimo de DQO
        
    return [dXdt, dSdt]


def simular_bioproceso_shp(dqo_ini, dqo_fin, t_het, t_fot, ph=4.96, brix=40.0):
    
    # Factor de penalización por pH (óptimo en 4.96)
    # Si el pH se aleja de 4.96, el crecimiento disminuye
    factor_ph = np.exp(-0.5 * (ph - 4.96)**2)
    
    params = {
        'mu_het': 0.05 * factor_ph, 
        'mu_fot': 0.015 * factor_ph,
        'Ks': 5.0,
        'Y_xs': 0.45
    }
    
    # Condición inicial: Biomasa 0.5 g/L y DQO inicial
    y0_het = [0.5, dqo_ini]
    
    # 1. Fase Heterotrófica
    t_eval_het = np.linspace(0, t_het, 100)
    sol_het = solve_ivp(
        ecuacion_shp, (0, t_het), y0_het, 
        args=('heterotrofia', params), t_eval=t_eval_het
    )
    
    # Transición de estados
    y0_fot = sol_het.y[:, -1]
    
    # 2. Fase Fotoinducida
    t_eval_fot = np.linspace(t_het, t_het + t_fot, 100)
    sol_fot = solve_ivp(
        ecuacion_shp, (t_het, t_het + t_fot), y0_fot, 
        args=('fotoinduccion', params), t_eval=t_eval_fot
    )
    
    # Consolidación de datos
    t_total = np.concatenate((sol_het.t, sol_fot.t))
    X_total = np.concatenate((sol_het.y[0], sol_fot.y[0]))
    S_total = np.concatenate((sol_het.y[1], sol_fot.y[1]))
    
    return t_total, X_total, S_total