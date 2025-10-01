function Aerodynamic_coefficients = Aero_LT_long(LT,state,controls,warnings)

LT.hc_points(LT.hc_points==inf) = 1000;
state.hc(state.hc==inf) = 1000;

% default_method = 'spline';
default_method = 'linear';
prevent_extrapolation = 1;

if LT.n_alpha == 1
    if warnings == 1
        warning('Only one data point for Alpha! keeping results constant for the only existing value')
    end
    LT1 = LT;
    LT1.Alpha_points = LT1.Alpha_points+1;
    LT = JoinLT(LT,LT1);
end

if LT.n_beta == 1
    if warnings == 1
        warning('Only one data point for Beta! keeping results constant for the only existing value')
    end
    LT1 = LT;
    LT1.Beta_points = LT1.Beta_points+1;
    LT = JoinLT_long(LT,LT1);
end

if LT.n_reynolds == 1
    if warnings == 1
        warning('Only one data point for Reynolds! keeping results constant for the only existing value')
    end
    LT1 = LT;
    LT1.Reynolds_points = LT1.Reynolds_points+1;
    LT = JoinLT(LT,LT1);
end

if LT.n_roll == 1
    if warnings == 1
        warning('Only one data point for Roll! keeping results constant for the only existing value')
    end
    LT1 = LT;
    LT1.Roll_points = LT1.Roll_points+1;
    LT = JoinLT_long(LT,LT1);
end

if LT.n_hc == 1
    if warnings == 1
        warning('Only one data point for h/c! keeping results constant for the only existing value')
    end
    LT1 = LT;
    LT1.hc_points = LT1.hc_points+1;
    LT = JoinLT(LT,LT1);
end

has_to_extrapolate = 0;


if ~(state.alpha >= min(LT.Alpha_points) && (state.alpha <= max(LT.Alpha_points)))
    if warnings == 1
        warning('outside alpha envelope!')
    end
    if prevent_extrapolation == 1
        state.alpha = max(min(LT.Alpha_points), min(state.alpha, max(LT.Alpha_points)));
    else
        has_to_extrapolate = 1;
    end
end

if ~(state.beta >= min(LT.Beta_points) && (state.beta <= max(LT.Beta_points)))
    if warnings == 1
        warning('outside beta envelope!')
    end
    if prevent_extrapolation == 1
        state.beta = max(min(LT.Beta_points), min(state.beta, max(LT.Beta_points)));
    else
        has_to_extrapolate = 1;
    end
end

if ~(state.reynolds >= min(LT.Reynolds_points) && (state.reynolds <= max(LT.Reynolds_points)))
    if warnings == 1
        warning('outside reynolds envelope!')
    end
    if prevent_extrapolation == 1
        state.reynolds = max(min(LT.Reynolds_points), min(state.reynolds, max(LT.Reynolds_points)));
    else
        has_to_extrapolate = 1;
    end
end

if ~(state.hc >= min(LT.hc_points) && (state.hc <= max(LT.hc_points)))
    if warnings == 1
        warning('outside h/c envelope!')
    end
    if prevent_extrapolation == 1
        state.hc = max(min(LT.hc_points), min(state.hc, max(LT.hc_points)));
    else
        has_to_extrapolate = 1;
    end
end

if ~(state.roll >= min(LT.Roll_points) && (state.roll <= max(LT.Roll_points)))
    if warnings == 1
        warning('outside roll envelope!')
    end
    if prevent_extrapolation == 1
        state.roll = max(min(LT.Roll_points), min(state.roll, max(LT.Roll_points)));
    else
        has_to_extrapolate = 1;
    end
end


if has_to_extrapolate == 1
    if warnings == 1
        warning('extrapolating envelope with spline method...')
    end
    Aerodynamic_coefficients.Cx = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cx, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
%     Aerodynamic_coefficients.Cy = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cy, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
    Aerodynamic_coefficients.Cz = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cz, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
    
    Aerodynamic_coefficients.CL = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CL, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');

%     Aerodynamic_coefficients.CDi = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CDi, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
    Aerodynamic_coefficients.CD = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CD, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');

%     Aerodynamic_coefficients.CMx = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMx, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
    Aerodynamic_coefficients.CMy = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMy, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
%     Aerodynamic_coefficients.CMz = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMz, state.alpha, state.beta, state.reynolds, state.hc, state.roll, 'spline');
else
    Aerodynamic_coefficients.Cx = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cx, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
%     Aerodynamic_coefficients.Cy = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cy, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
    Aerodynamic_coefficients.Cz = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.Cz, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
    
    Aerodynamic_coefficients.CL = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CL, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);

%     Aerodynamic_coefficients.CDi = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CDi, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
    Aerodynamic_coefficients.CD = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CD, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);

%     Aerodynamic_coefficients.CMx = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMx, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method');
    Aerodynamic_coefficients.CMy = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMy, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
%     Aerodynamic_coefficients.CMz = interpn(LT.Alpha_points, LT.Beta_points, LT.Reynolds_points, LT.hc_points, LT.Roll_points, LT.CMz, state.alpha, state.beta, state.reynolds, state.hc, state.roll, default_method);
end

end