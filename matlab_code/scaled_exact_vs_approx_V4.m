clear all

w = warning ('off','all');

OUTPUT_FOLDER_PDF = '/home/vilc/Dropbox/Aplicativos/Overleaf/Epidemics and Strategic Attackers (IEEE Access)/img/';
save_file = true;

mu_vec_all     = [17.9593, 18.1603, 18.0462, 17.4592, ...
                 154.8883, 44.7099, 21.4111, 15.7172, ...
                 122.9877, 43.5209, 20.9333, 2.8819];
             
gamma_vec_all  = [1.0071 , 1.0092 , 1.0148 , 1.0383 , ...
                 1.0262  , 1.0262 , 1.0148 , 1.0071 , ...
                 1.0061  , 1.0148 , 1.0148 , 1.0171];

lambda_vec = [1500];

vec_N = [ 10,  28,  46,  64,  82, 100, 200, 300, 400, 500];
alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'];

simul_alpha = [8 , 20,  50,  500];
simul_beta  = [5 , 32, 200, 2000];
simul_tau   = [18, 40,  65,  260];

k = 0;
txt = sprintf('$\\Lambda$ & $N_{min}$ & $\\rho(N_{min})$ & $\\mu$ & $\\rho_{min}$ & $N(\\rho_{min})$ & $\\gamma$ \\\\ \n');

txt_latex_aux    = sprintf('\\hspace{-0.6cm}\\includegraphics[width=0.35\\columnwidth] \n');

txt_latex_lin_1a = '';
txt_latex_lin_1b = '';
txt_latex_lin_1c = '';

txt_latex_lin_2a = '';
txt_latex_lin_2b = '';
txt_latex_lin_2c = '';

txt_latex_lin_3a = '';
txt_latex_lin_3b = '';
txt_latex_lin_3c = '';

txt_latex_lin_4a = '';
txt_latex_lin_4b = '';
txt_latex_lin_4c = '';


% Language: 0 - defaut (portuguese); 1 - English
lang = 1;
if lang == 1
    label_inter_conf  = 'Conf. inter. (95%)';
    label_simul_infec = 'infected (simulation)';
    label_simul_end   = 'infected endogenously';
    label_simul_exo   = 'infected exogenously';
    label_simul_off   = 'Simul. Turn Off';
    label_exato       = 'Exact';
    label_approx      = 'infected (analytical model)';
else
    label_inter_conf  = 'Inter. conf.(95%)';
    label_simul_infec = 'Simul. Infectado';
    label_simul_end   = 'Simul. Endógeno';
    label_simul_exo   = 'Simul. Exógeno';
    label_simul_off   = 'Simul. Desligado';
    label_exato       = 'Exato';
    label_approx      = 'Aprox. Heurística';
end


for i = 1:length(mu_vec_all)
    
    j = mod(i-1,4);
    if j == 0
        k = k+1;
    end
    
    filename = sprintf('exec_counter-240_param-%d00%d.csv',k,j);
    disp(filename)
    M = csvread(filename);
    
    factor_mu    = 0.5;
    factor_gamma = 1.00225;
    [lambda_3, mu_3, gamma_3] = parameters(M, factor_mu, factor_gamma);
    
    %mu_vec    = [mu_vec_all(i)];
    %gamma_vec = [gamma_vec_all(i)];
    labda_vec  = [lambda_3];
    mu_vec     = [mu_3];
    gamma_vec  = [gamma_3];
    
    aux1 = scaledSISExact(lambda_vec, mu_vec, gamma_vec, vec_N);
    rhoA = squeeze(aux1(1,1,1,:));

    [aux2, aux3] = scaledSISAprox(lambda_vec, mu_vec, gamma_vec, vec_N);
    rho0 = squeeze(aux2(1,1,1,:));
    rho1 = squeeze(aux3(1,1,1,:));
    
    if min(rho1) < 0 || max(rho1) > 1
        rhoB = rho0;
    else
        rhoB = rho1;
    end

    f = figure('visible','off');
    
    x_m = [M(:,1)', flipud(M(:,1))'];
    Mp = M(:,3)+M(:,7);
    Md = M(:,3)-M(:,7);
    y_m = [Mp', flipud(Md)'];
    %fill(x_m,y_m, 'y', 'edgecolor', 'none', 'facealpha', 0.3, 'DisplayName', label_inter_conf)
    plot(vec_N, M(:,3), 'r', 'DisplayName', label_simul_infec)
    hold on
    plot(vec_N, M(:,4), 'r:', 'DisplayName', label_simul_end)
    hold on
    plot(vec_N, M(:,5), 'r--', 'DisplayName', label_simul_exo)
    hold on
    %plot(vec_N, M(:,6), 'g', 'DisplayName', label_simul_off)
    %hold on
    %plot(vec_N, rhoA, 'm'  , 'DisplayName', label_exato)
    %hold on
    plot(vec_N, rhoB, 'b-.', 'DisplayName', label_approx)
    hold on
    
    if i < length(mu_vec_all)/3 
        if lang == 1
            ylabel('Infection probability', 'FontSize', 20);
        else
            ylabel('Proporção de nós infectados', 'FontSize', 20)
        end
    elseif i == length(mu_vec_all)/3 || i == length(mu_vec_all)*2/3 || i == length(mu_vec_all)
        if i == length(mu_vec_all)/3
            if lang == 1
                ylabel('Infection probability', 'FontSize', 20);
            else
                ylabel('Proporção de nós infectados', 'FontSize', 20)
            end
        end
        if lang == 1
            xlabel('Number of vulnerable nodes', 'FontSize', 20);
        else
            xlabel('Número de nós não vacinados', 'FontSize', 20);
        end
    end
    
    
    set(gca,'FontSize',10)
    ylim([0, 1]);
    xlim([0,500]);
    if i == length(mu_vec_all)
        lgd = legend('FontSize',7,'Location','east', 'Orientation','vertical', 'AutoUpdate','off','Box','off');
    %elseif i == length(mu_vec_all)*2/3
        %lgd = legend('FontSize',7,'Position',[0.2 0.42 0.2 0.01], 'Orientation','vertical', 'AutoUpdate','off','Box','off');
    %elseif i == length(mu_vec_all)/3
    %    lgd = legend('FontSize',7,'Location','southeast', 'Orientation','vertical', 'AutoUpdate','off','Box','off');
    end
    fill(x_m,y_m, 'y', 'edgecolor', 'none', 'facealpha', 0.3) 
    hold off

    grid();
    %plot(N(1:T),0.6 .* ones(1,T), 'r')

    str_file_pdf = sprintf('fig_%s_%d00%d_v4_lambda%0.0f_mu%0.4f_gamma%0.6f_iter_%d_rho0_0',alpha(i), k, j, lambda_vec(1), mu_vec(1), gamma_vec(1), 2);

    if save_file
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
        %disp(str_file_std)
        fig = gcf;
        
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 4.2];
        %print(fig,str_file_std,'-dpng','-r300');  
        
        %fig.PaperPositionMode = 'auto';
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
    
    [~, g_idx] = min(M(:,3));   
    txt = sprintf('%s %6.1f &  %d & %6.4f & %7.4f & %6.4f & %d &  %6.4f \\\\ \n',txt, lambda_3, M(1,1), M(1,3), mu_3, M(g_idx,3), M(g_idx,1) , gamma_3);
    
    if (k == 3)
        fim = '\\';
    else
        fim = '&';
    end
    if (j == 0)
        txt_latex_lin_1a = sprintf('%s%s {img/%s.pdf} %s \n', txt_latex_lin_1a, txt_latex_aux, strrep(str_file_pdf,'.','_'), fim);
        if (k ==3)
            txt_latex_lin_1b = sprintf('%s (%s) $\\alpha = %3d \\times 10^{-5}$ &\n (%s) $\\beta  = %4d \\times 10^{-2}$ &\n (%s) $\\tau   = %d$\\\\ \n', txt_latex_lin_1b, 'a', simul_alpha(j+1), 'b', simul_beta(j+1), 'c', simul_tau(j+1));
        end
        txt_latex_lin_1c = sprintf('%s $\\mu = %8.4f$, $\\gamma = %6.4f$ %s \n', txt_latex_lin_1c, mu_3, gamma_3, fim);
    elseif (j == 1)
        txt_latex_lin_2a = sprintf('%s%s {img/%s.pdf}  %s  \n', txt_latex_lin_2a, txt_latex_aux, strrep(str_file_pdf,'.','_'), fim);
        if (k ==3)
            txt_latex_lin_2b = sprintf('%s (%s) $\\alpha = %3d \\times 10^{-5}$ &\n (%s) $\\beta  = %4d \\times 10^{-2}$ &\n (%s) $\\tau   = %d$\\\\ \n', txt_latex_lin_2b, 'd', simul_alpha(j+1), 'e', simul_beta(j+1), 'f', simul_tau(j+1));
        end
        txt_latex_lin_2c = sprintf('%s $\\mu = %8.4f$, $\\gamma = %6.4f$ %s \n', txt_latex_lin_2c, mu_3, gamma_3, fim);
    elseif (j == 2)
        txt_latex_lin_3a = sprintf('%s%s {img/%s.pdf}  %s  \n', txt_latex_lin_3a, txt_latex_aux, strrep(str_file_pdf,'.','_'), fim);
        if (k ==3)
            txt_latex_lin_3b = sprintf('%s (%s) $\\alpha = %3d \\times 10^{-5}$ &\n (%s) $\\beta  = %4d \\times 10^{-2}$ &\n (%s) $\\tau   = %d$\\\\ \n', txt_latex_lin_3b, 'g', simul_alpha(j+1), 'h', simul_beta(j+1), 'i', simul_tau(j+1));
        end
        txt_latex_lin_3c = sprintf('%s $\\mu = %8.4f$, $\\gamma = %6.4f$ %s \n', txt_latex_lin_3c, mu_3, gamma_3, fim);
    elseif (j == 3)
        txt_latex_lin_4a = sprintf('%s%s {img/%s.pdf}  %s  \n', txt_latex_lin_4a, txt_latex_aux, strrep(str_file_pdf,'.','_'), fim);
        if (k ==3)
            txt_latex_lin_4b = sprintf('%s (%s) $\\alpha = %3d \\times 10^{-5}$ &\n (%s) $\\beta  = %4d \\times 10^{-2}$ &\n (%s) $\\tau   = %d$\\\\ \n', txt_latex_lin_4b, 'j', simul_alpha(j+1), 'k', simul_beta(j+1), 'l', simul_tau(j+1));
        end
        txt_latex_lin_4c = sprintf('%s $\\mu = %8.4f$, $\\gamma = %6.4f$ %s \n', txt_latex_lin_4c, mu_3, gamma_3, fim);
    end
    
end
disp(txt)

disp(txt_latex_lin_1a)
disp(txt_latex_lin_1b)
disp(txt_latex_lin_1c)

disp(txt_latex_lin_2a)
disp(txt_latex_lin_2b)
disp(txt_latex_lin_2c)

disp(txt_latex_lin_3a)
disp(txt_latex_lin_3b)
disp(txt_latex_lin_3c)


disp(txt_latex_lin_4a)
disp(txt_latex_lin_4b)
disp(txt_latex_lin_4c)

w = warning ('on','all');

function [lambda_i, mu_i, gamma_i] = parameters(vec_M, factor_mu, factor_gamma)
    [~, idx_min] = min(vec_M(:,3));
    
    
    lambda_i = 1500;
    
    mu_i = factor_mu * lambda_i * (1-vec_M(1,3))/(vec_M(1,1)*vec_M(1,3));
    
    m = 5 * vec_M(idx_min,1);
    gamma_i = factor_gamma * (m^(1/m));
end