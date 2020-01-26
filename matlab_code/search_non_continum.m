clear all

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';

N     = [1:200];
N = 200;
%gamma1_vec = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
gamma1_vec = [1.09];
gamma1 = 1.09;
mu1   = 1.0;
%lambda = 10 .* (N.^(-1));
lambda = 10;
%rho0 = zeros(1, length(N));4
rho0 = 0;
T = 100;

iter = 10;


f = figure('visible','on');
hold on;

%ylim([0, 1]);
%xlim([1,T]);
for gamma1 = gamma1_vec
    

    for n = 2:N
        rho2(n, 1) = next_rho_v2(lambda/n, rho0, mu1, gamma1, n-1);
        for i = 1:iter
            rho2(n, i+1) = next_rho_v2(lambda/n, rho2(n, i), mu1, gamma1, n-1);
        end
    end
    
    for i = 1:iter
        plot(1:N, rho2(:,i))
        hold on
    end

%X = 1:200;
%Y = zeros(1,200);
%    for i = 1:iter
%        Y = 1.09 .^ (-1 .* ((X - 1) .* Y));
%        plot(X, Y, 'DisplayName',sprintf('\\iter=%d',i))
%    end


end



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
    if rho_aux < 0.0
        rho_aux = 0.0;
    elseif rho_aux > 1.0
        rho_aux = 1.0;
    end
    
    txt = sprintf('N: %d; rho: %f;\t \\gamma^{-\\rho g}: %f;\t \\mu/\\lambda = %f',grade, rho_aux, gamma_exp_neg_rho_g, mu_over_lambda);
    disp(txt);
    rho = rho_aux;
end