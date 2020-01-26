function [rho_end0, rho_end1] = scaledSISAprox(vec_lambda, vec_mu, vec_gamma, vec_N)

   %% Newton approximation
    % Lambda represents the exogenous infection factor
    qtd_lambda  = length(vec_lambda);
    % healing factor
    qtd_mu      = length(vec_mu);
    % Gamma represents the endogenous infection factor
    qtd_gamma   = length(vec_gamma);
    %  N - represents the total susceptibles (individuals)
    qtd_N       = length(vec_N);
    
    rho0 = -1 * ones(qtd_lambda, qtd_mu, qtd_gamma, qtd_N);
    rho1 = -1 * ones(qtd_lambda, qtd_mu, qtd_gamma, qtd_N);

    ilambda = 0;
    for lambda1 = vec_lambda
        ilambda = ilambda +1;
        
        imu = 0;
        for mu1 = vec_mu
            imu = imu + 1;
            
            igamma = 0;
            for gamma1 = vec_gamma
                igamma = igamma +1;
                
                iN = 0;
                for n = vec_N
                    iN = iN + 1; 
                    rho0(ilambda, imu, igamma, iN) = rho_zero_2iter(lambda1/n, mu1, gamma1, n-1);
                    rho1(ilambda, imu, igamma, iN) = rho_one_2iter (lambda1/n, mu1, gamma1, n-1);
                end



            end
        end
    end
    
    rho_end0 = rho0;
    rho_end1 = rho1;
end