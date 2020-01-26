clear all

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';

N     = [1:200];
gamma1_vec = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
gamma1 = 1.09;
mu1   = 1.0;
lambda = 10 .* (N.^(-1));
rho0 = 0.0.*ones(1, length(N));
%rho0(1,1) = 0.1;
rho_bef = rho0;
T = 200;

iter = 2;


f = figure('visible','on');
hold on;

ylim([0, 1]);
xlim([1,T]);
for gamma1 = gamma1_vec
    rho2 = next_rho(lambda, rho0, mu1, gamma1, N);
    %rho2 = next_rho(lambda, 0 .* rho0, mu1, gamma1, N);
    %if (rho2 <=0)
    %    rho2 = next_rho(lambda, 1 .* rho0, mu1, gamma1, N);
    %end

    for i = [1:iter]
        %rho_bef = rho2;
        rho2 = next_rho(lambda, rho2, mu1, gamma1, N);
        
        for j = 1:length(rho2)
            %if rho2(j) > 0 && rho2(j) < 1
                rho_bef(j) = rho2(j);
            %end
        end
        %if (min(rho2) < 0) error('negative');
        %end
    end
    
    if gamma1 == 1.09
        plot(N(1:T), rho_bef(1:T),'b', 'DisplayName', sprintf('\\gamma=%0.2f', gamma1));
    else
        plot(N(1:T), rho_bef(1:T),'--', 'DisplayName', sprintf('\\gamma=%0.2f', gamma1));
    end
end
lgd = legend('FontSize',12,'Location','southeast', 'Orientation','vertical','AutoUpdate','off');
grid();
plot(N(1:T),0.6 .* ones(1,T), 'r')

str_file_pdf = sprintf('approx_newton_lambda%0.2f_gamma%0.2f_iter_%d', lambda(1), gamma1, iter);

if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [fig_pos(3) fig_pos(4)];
    print (fig,str_file_std,'-dpdf');
end

