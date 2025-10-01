function[Aerodynamic_coefficients] = get_FDM_data(alpha,hc,airspeed,FDM)

state.alpha = alpha;
state.beta = 0;
state.reynolds = (airspeed*FDM.reference.chord*FDM.reference.rho)/FDM.reference.dynamic_viscosity;
state.hc = hc;
state.roll = 0;

controls.aileron = 0;
controls.elevator = 0;
controls.rudder = 0;

Aerodynamic_coefficients = Aero_LT_long(FDM,state,controls,0);
end