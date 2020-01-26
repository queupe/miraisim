%% Using Newton's approximation with close formulas

clear all

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';

T          = 200;
N          = 1:T;
gamma1_vec = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
mu1        = 1.0;
lambda1    = 10;

rho0 = zeros(1,T);
rho1 = zeros(1,T);

f = figure('visible','on');
hold on;

ylim([0, 1]);
xlim([1,T+50]);
for gamma1 = gamma1_vec
    for n = N
        rho0(n) = rho_zero_3iter(lambda1/n, mu1, gamma1, n-1);
        rho1(n) = rho_one_3iter (lambda1/n, mu1, gamma1, n-1);
    end

    for n = N
        txt = sprintf('gamma=%f;\t N=%d;\t rho0(0)=%f;\t rho0(1)=%f ', gamma1, n, rho0(n), rho1(n));
        disp(txt);
    end

    plot(N(1:T), rho0(1:T),'--', 'DisplayName', sprintf('\\gamma=%0.2f and \\rho_0=0', gamma1));
    hold on


end
for gamma1 = gamma1_vec
    for n = N
        rho1(n) = rho_one_3iter (lambda1/n, mu1, gamma1, n-1);
    end
    
    plot(N(1:T), rho1(1:T),':', 'DisplayName', sprintf('\\gamma=%0.2f and \\rho_0=1', gamma1));
    hold on
end

lgd = legend('FontSize',8,'Location','southeast', 'Orientation','vertical','AutoUpdate','off');
grid();
%plot(N(1:T),0.6 .* ones(1,T), 'r')

str_file_pdf = sprintf('approx_newton_closed_form_lambda%0.2f_gamma%0.2f_iter_%d', lambda1, gamma1, 3);

if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [fig_pos(3) fig_pos(4)];
    print (fig,str_file_std,'-dpdf');
end

