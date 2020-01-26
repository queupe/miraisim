function rho = rho_zero_2iter(lambda_i, mu_i, gamma_i, nodes)

% \rho_{1} = \frac{ \lambda - \mu \gamma^{-\rho_{0} n }  \left( \rho_{0}^{2} n  \ln \gamma     \right) }  
%                 { \lambda - \mu \gamma^{-\rho_{0} n }  \left( \rho_{0}     n  \ln \gamma  -1 \right) }  
%	       = \frac{ \lambda       \right) }  
%                 { \lambda - \mu \right) }  

    rho_1     = lambda_i / (lambda_i + mu_i);


% \rho_{2} &=& \frac{ \lambda - \mu \gamma^{-\rho_{1} n } \left( \rho_{1}^{2} n \ln \gamma \right) }  
%                   { \lambda - \mu \gamma^{-\rho_{1} n } \left( \rho_{1}     n \ln \gamma -1 \right) }
    
    % \mu \gamma^{-\rho_{1} n }
    mu_gamma_exp_rho1_n = mu_i * gamma_i^(-1 * rho_1 * nodes);
    % \rho_{1}     n \ln \gamma -1
    rho1_n_ln_gamma = rho_1 * nodes * log(gamma_i);
    
    rho2_sup = lambda_i - mu_gamma_exp_rho1_n * rho1_n_ln_gamma * rho_1;
    rho2_inf = lambda_i - mu_gamma_exp_rho1_n * (rho1_n_ln_gamma -1 );
    
    rho = rho2_sup/rho2_inf;
end