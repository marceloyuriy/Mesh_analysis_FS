function LT = JoinLT_long(LT1,LT2)

Alpha_points = sort(unique([LT1.Alpha_points LT2.Alpha_points]));
Beta_points = sort(unique([LT1.Beta_points LT2.Beta_points]));
Reynolds_points = sort(unique([LT1.Reynolds_points LT2.Reynolds_points]));
hc_points = sort(unique([LT1.hc_points LT2.hc_points]));
Roll_points = sort(unique([LT1.Roll_points LT2.Roll_points]));


n_alpha = size(Alpha_points,2);
n_beta = size(Beta_points,2);
n_reynolds = size(Reynolds_points,2);
n_hc = size(hc_points,2);
n_roll = size(Roll_points,2);


LT.n_alpha = n_alpha;
LT.n_beta = n_beta;
LT.n_reynolds = n_reynolds;
LT.n_hc = n_hc;
LT.n_roll = n_roll;

LT.Alpha_points = Alpha_points;
LT.Beta_points = Beta_points;
LT.Reynolds_points = Reynolds_points;
LT.hc_points = hc_points;
LT.Roll_points = Roll_points;


for index_alpha=1:n_alpha
    for index_beta=1:n_beta
        for index_reynolds=1:n_reynolds
            for index_hc=1:n_hc
                for index_roll=1:n_roll
                
                    alpha_match = LT2.Alpha_points == Alpha_points(index_alpha);
                    beta_match =  LT2.Beta_points == Beta_points(index_beta);
                    reynolds_match = LT2.Reynolds_points == Reynolds_points(index_reynolds);
                    hc_match = LT2.hc_points == hc_points(index_hc);
                    roll_match = LT2.Roll_points == Roll_points(index_roll);
    
                    if all(~alpha_match) | all(~beta_match) | all(~reynolds_match) | all(~hc_match) | all(~roll_match)
                        skip =1;
                    else
                    
    
                    LT.Cx(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.Cx(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
%                     LT.Cy(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.Cy(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    LT.Cz(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.Cz(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
                    LT.CL(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CL(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
%                     LT.CDi(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CDi(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    LT.CD(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CD(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
%                     LT.CMx(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CMx(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    LT.CMy(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CMy(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
%                     LT.CMz(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT2.CMz(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    end
                    %
    
    
                    alpha_match = LT1.Alpha_points == Alpha_points(index_alpha);
                    beta_match =  LT1.Beta_points == Beta_points(index_beta);
                    reynolds_match = LT1.Reynolds_points == Reynolds_points(index_reynolds);
                    hc_match = LT1.hc_points == hc_points(index_hc);
                    roll_match = LT1.Roll_points == Roll_points(index_roll);
    
                    if all(~alpha_match) | all(~beta_match) | all(~reynolds_match) | all(~hc_match) | all(~roll_match)
                        skip =1;
                    else
    
                    LT.Cx(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.Cx(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
%                     LT.Cy(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.Cy(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    LT.Cz(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.Cz(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
                    LT.CL(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CL(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
                    LT.CD(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CD(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
%                     LT.CDo(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CDo(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
        
%                     LT.CMx(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CMx(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    LT.CMy(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CMy(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
%                     LT.CMz(index_alpha,index_beta,index_reynolds,index_hc,index_roll) = LT1.CMz(alpha_match,beta_match,reynolds_match,hc_match,roll_match);
                    end

                end
            end
        end
    end
end


end