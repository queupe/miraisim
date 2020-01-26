function rho = next_rho(lambda1, rho1, mu1, gamma1, grade)

    gamma_aux = gamma1.^((-1 .* grade) .* rho1);

    factor1 = (rho1.^2).* (gamma_aux);
    %factor2 = 

    superior = lambda1 - (factor1) .* (grade .* (mu1 *  log(gamma1)));
    inferior = lambda1 - (rho1.* gamma_aux)   .* (grade .* (mu1  * log(gamma1))) + mu1 .* gamma_aux;
    rho = superior./inferior;
end