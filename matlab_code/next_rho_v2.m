function rho = next_rho_v2(lambda1, rho_before1, mu1, gamma1, grade)

    gamma_exp_neg_rho_g = gamma1.^((-1 .* grade) .* rho_before1);
    %disp (gamma_exp_neg_rho_g);
    %disp(grade)
    
    mu_over_lambda = mu1/lambda1;
    %disp (mu_over_lambda);
    
    rho_grade_ln_gamma = rho_before1 * grade * log(gamma1);
    %disp(rho_grade_ln_gamma);
    
    f_rho = rho_before1 *(1 + mu_over_lambda * gamma_exp_neg_rho_g ) -1;
    f_lin_rho = 1 + mu_over_lambda * gamma_exp_neg_rho_g *(1 - rho_grade_ln_gamma);
    
    
    rho_aux = rho_before1 - f_rho/f_lin_rho;
    %if rho_aux < 0.0
    %    rho_aux = 0.0;
    %elseif rho_aux > 1.0
    %    rho_aux = 1.0;
    %end
    
    txt = sprintf('N: %d; rho: %f;\t \\gamma^{-\\rho g}: %f;\t \\mu/\\lambda = %f',grade, rho_aux, gamma_exp_neg_rho_g, mu_over_lambda);

    disp(txt);
    rho = rho_aux;
end