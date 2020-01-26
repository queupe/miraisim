close all
clear all

%w = warning ('off','all');

OUTPUT_FOLDER_PDF = '/home/vilc/Dropbox/Aplicativos/Overleaf/Epidemics and Strategic Attackers (IEEE Access)/img/';
save_file = true;


% Language: 0 - defaut (portuguese); 1 - English
lang = 1;
if lang == 1
    label_inter_conf  = 'Conf. inter. (95%)';
    label_simul_infec = 'Simul. Infected';
    label_simul_end   = 'Simul. Endogenous';
    label_simul_exo   = 'Simul. Exogenous';
    label_simul_off   = 'Simul. Turn Off';
    label_exato       = 'Exact';
    label_approx      = 'Heuristic Approx.';
else
    label_inter_conf  = 'Inter. conf.(95%)';
    label_simul_infec = 'Simul. Infectado';
    label_simul_end   = 'Simul. Endógeno';
    label_simul_exo   = 'Simul. Exógeno';
    label_simul_off   = 'Simul. Desligado';
    label_exato       = 'Exato';
    label_approx      = 'Aprox. Heurística';
end




    f = figure('visible','off');
    
    x = [-10, -5];
    y = [-10, -5];
    
    plot(x, y, 'r'  , 'DisplayName', label_simul_infec)
    hold on
    plot(x, y, 'r:' , 'DisplayName', label_simul_end)
    hold on
    plot(x, y, 'r--', 'DisplayName', label_simul_exo)
    hold on
    plot(x, y, 'b-.', 'DisplayName', label_approx)
    hold off
    
    
    set(gca,'FontSize',1)
    ylim([0, 1]);
    xlim([0,200]);
    lgd = legend('FontSize',12,'Location','best', 'Orientation','vertical', 'AutoUpdate','off','Box','off');

    %axis off
    %grid();

    str_file_pdf = sprintf('fig_legend_v4_lambda');

    if save_file
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
        %disp(str_file_std)
        fig = gcf;
        
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 7.2 4.2];
        %print(fig,str_file_std,'-dpng','-r300');  
        
        %fig.PaperPositionMode = 'auto';
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)), (fig_pos(4))];
        print (fig,str_file_std,'-dpdf');
    end
    



