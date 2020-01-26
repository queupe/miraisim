clear all

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';
save_file = true;

mu_vec_all     = [17.9593, 18.1603, 18.0462, 17.4592, 
                 154.8883, 44.7099, 21.4111, 15.7172, 
                 122.9877, 43.5209, 20.9333, 2.8819];
             
gamma_vec_all  = [1.0071 , 1.0092 , 1.0148 , 1.0383 , 
                 1.0262  , 1.0262 , 1.0148 , 1.0071 , 
                 1.0061  , 1.0148 , 1.0148 , 1.0171];

lambda_vec = [1500];

vec_N = [ 10,  28,  46,  64,  82, 100, 200, 300, 400, 500];
alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'];




k = 0;
for i = 1:length(mu_vec_all)
    
    j = mod(i-1,4);
    if j == 0
        k = k+1;
    end
    
    filename = sprintf('exec_counter-240_param-%d00%d.csv',k,j);
    disp(filename)
    M = csvread(filename);
    
    mu_vec    = [mu_vec_all(i)];
    gamma_vec = [gamma_vec_all(i)];
    
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
    plot(vec_N, M(:,3), 'r', 'DisplayName', 'Simul. Infec.')
    hold on
    plot(vec_N, M(:,4), 'r:', 'DisplayName', 'Simul. End.')
    hold on
    plot(vec_N, M(:,5), 'r--', 'DisplayName', 'Simul. Exo.')
    hold on
    plot(vec_N, M(:,6), 'g', 'DisplayName', 'Simul. Desl.')
    hold on
    plot(vec_N, rhoA, 'm'  , 'DisplayName', 'Exact')
    hold on
    plot(vec_N, rhoB, 'c--', 'DisplayName', 'Aprox. Heu')
    hold off
    
    xlabel('Número de nós')
    ylabel('proporção de infectados')
    
    ylim([0, 1]);
    lgd = legend('FontSize',10,'Location','east', 'Orientation','vertical');
    grid();
    %plot(N(1:T),0.6 .* ones(1,T), 'r')

    str_file_pdf = sprintf('fig_%s_%d00%d_v1_lambda%0.0f_mu%0.4f_gamma%0.6f_iter_%d_rho0_0',alpha(i), k, j, lambda_vec(1), mu_vec(1), gamma_vec(1), 2);

    if save_file
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
        %disp(str_file_std)
        fig = gcf;
        fig.PaperPositionMode = 'auto';
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
    
end

