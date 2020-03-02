clear all
syms cgamma n d

v_lambda = 10;
v_mu     = 1;
v_gamma  = 2.39;

% Language: 0 - defaut (portuguese); 1 - English
lang = 1;

% Figure to presentation -> 0; to paper -> 1
fig_pdf = 1; 

tot_user = 8;
vec_elem = 1:tot_user;
degree_fully      = [0/1, 2/2, 4/3, 8/4, 12/5, 18/6, 24/7, 32/8];
degree_3          = [0, 1, 2, 2, 3 * ones(1,tot_user-4)];
degree_avg        = [0/1, 2/2, 4/3, 8/4, 10/5, 14/6, 16/7, 20/8];
degree_avg_ciclic = [0/1, 2/2, 4/3, 8/4, 12/5, 18/6, 18/7, 24/8];
save_file = true;
%OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';
%OUTPUT_FOLDER_PDF = '/home/vilc/Dropbox/UFRJ/followavoidcrowd/epssis/paper/epidemic_model_approx/edition/model/';
OUTPUT_FOLDER_PDF = '/home/vilc/Documents/UFRJ/git/mirai_graph/rhoappr/';


%% closed form d*=d/2 (d -> degree)
rho=((v_lambda/(n*v_mu))*(cgamma^(d/2)))/(1+(v_lambda/(n*v_mu))*(cgamma^(d/2)));
%rho109=eval(subs(rho,{n,cgamma,d},{vec_elem,v_gamma,degree_avg})); % degree d = 3
%rho109=eval(subs(rho,{n,cgamma,d},{vec_elem,v_gamma,vec_elem/2})); % degree d = N/2
%rho109=eval(subs(rho,{n,cgamma,d},{vec_elem,v_gamma,degree_avg_ciclic})); % degree ciclic
rho109=eval(subs(rho,{n,cgamma,d},{vec_elem,v_gamma,degree_fully})); % degree fully
if lang == 1
    text_lang_001 = '\rho(n), d*=d/2';
else
    text_lang_001 = '\rho(n), d*=d/2';
end

hold on;
plot(rho109,'-', 'DisplayName', text_lang_001);

%% closed form d*=d (d -> degree)
rho2t   = ((v_lambda/(n*v_mu))*(cgamma^(d)))/(1+(v_lambda/(n*v_mu))*(cgamma^(d)));
%rho1092t=eval(subs(rho2t,{n,cgamma,d},{vec_elem,v_gamma,degree_avg})); % degree d = 3
%rho1092t= eval(subs(rho2t,{n,cgamma,d},{vec_elem,v_gamma,vec_elem/2})); % degree d = N/2
%rho1092t=eval(subs(rho2t,{n,cgamma,d},{vec_elem,v_gamma,degree_avg_ciclic})); % degree ciclic
rho1092t=eval(subs(rho2t,{n,cgamma,d},{vec_elem,v_gamma,degree_fully})); % degree fully
if lang == 1
    text_lang = '\rho(n), d*=d';
else
    text_lang = '\rho(n), d*=d';
end

hold on;
plot(rho1092t,'.-', 'DisplayName', text_lang);

%% Exact value

%f = @connection_fully;
%f = @connection_bipartite_d;
f = @connection_bipartite_knm;
%f = @connection_star;

fprintf("Partial results on program\n");
rho109b_aux = scaledSISExact_allTopologies_v2(v_lambda, v_mu, v_gamma, vec_elem, f);
rho109b = squeeze(rho109b_aux(1,1,1,:));
rho109b = rho109b';

if lang == 1
    text_lang = '\rho(n)';
else
    text_lang = '\rho(n)';
end

hold on;
plot(rho109b, 'DisplayName', text_lang);

%% Best approximation
index        = zeros(1,length(vec_elem));
rho109approx = zeros(1,length(vec_elem));

for nusers=vec_elem
	clear currho;
	factor_int = 8;
    currho = zeros(1,factor_int*nusers +1);
    for dege_app=0:1/factor_int:nusers
		currho(factor_int*dege_app+1)=((v_lambda/(nusers*v_mu))*(v_gamma^(dege_app)))/(1+((v_lambda/(nusers*v_mu))*(v_gamma^(dege_app))));        
    end
    
	% approxatexp(nusers)=currho(max(floor(expinf(nusers)-2),1));
	[c, index(nusers)] = min(abs(currho-rho109b(nusers)));
	rho109approx(nusers)=currho(index(nusers));
end


if lang == 1
    text_lang = '\rho(n), optimal d*';
else
    text_lang = '\rho(n), melhor aprox.';
end

hold on;
plot(rho109approx,'*', 'DisplayName', text_lang);

%% Closing plot
lgd = legend('FontSize',7,'Location','southeast', 'Orientation','vertical');
if lang == 1
    xlabel('Number of vulnerable nodes','FontSize',14);
    ylabel('Infection probability','FontSize',14);
else
    xlabel('Número de nós vulneráveis','FontSize',14);
    ylabel('Probabilidade de Infecção','FontSize',14);
end
%ylim([0.7,1])
hold off

%% Saving file
str_file_pdf = sprintf('aproximacao_n_star');
if save_file
    fig = gcf;
    if fig_pdf == 0
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.png');
        fig.PaperUnits = 'inches';
        fig.PaperPosition = [0 0 6 3];
        print(fig,str_file_std,'-dpng','-r300');
    else
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        %fig.PaperPositionMode = 'auto';
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
end

%% Checking with Markov Chain
rho_mc = zeros(1,4);
fprintf("Partial results on Markov Chain\n");
% One vulnerable node:
nodes1   = 1;
m_lambda = v_lambda;
pi1      = zeros(1, nodes1+1);
pi1(1)   = v_mu;
pi1(2)   = m_lambda;

rho_mc(1) = ((pi1/sum(pi1)) * [0:nodes1]')/nodes1;

fprintf("N=%d lamb=%4.1f mu=%3.1f gamma=%4.2f", nodes1, m_lambda, v_mu, v_gamma)
%fprintf("N=%d",nodes1)
for ch = 1:length(pi1)
    fprintf("\t \\tilde{\\pi_%d}=%.3f",ch, pi1(ch))
end
fprintf("\n")

% Two vulnerable nodes:
nodes2   = 2;
m_lambda = v_lambda/2;
pi2      = zeros(1, nodes2+1);
pi2(1)   = 1;
pi2(2)   = 2 * m_lambda / v_mu;
pi2(3)   = (m_lambda^2) * v_gamma/ (v_mu^2);

rho_mc(2) = ((pi2/sum(pi2)) * [0:nodes2]')/nodes2;

fprintf("N=%d lamb=%4.1f mu=%3.1f gamma=%4.2f", nodes2, m_lambda, v_mu, v_gamma)
%fprintf("N=%d",nodes2)
for ch = 1:length(pi2)
    fprintf("\t \\tilde{\\pi_%d}=%.3f",ch, pi2(ch))
end
fprintf("\n")

% Three vulnerable nodes:
nodes3   = 3;
m_lambda = v_lambda/nodes3;
pi3      = zeros(1, nodes3+1);
pi3(1)   = 1;
pi3(2)   = 3 * m_lambda / v_mu;
pi3(3)   = ((m_lambda^2) * (1 + (2 * v_gamma))) / v_mu^2;
pi3(4)   = ((m_lambda^3) * (v_gamma^2)) / v_mu^3;

rho_mc(3) = ((pi3/sum(pi3)) * [0:nodes3]')/nodes3;

fprintf("N=%d lamb=%4.1f mu=%3.1f gamma=%4.2f", nodes3, m_lambda, v_mu, v_gamma)
%fprintf("N=%d",nodes3)
for ch = 1:length(pi3)
    fprintf("\t \\tilde{\\pi_%d}=%.3f",ch, pi3(ch))
end
fprintf("\n")


% Four vulnerable nodes:
nodes4   = 4;
m_lambda = v_lambda/nodes4;
pi4      = zeros(1, nodes4+1);
pi4(1)   = 1;
pi4(2)   = 4 * m_lambda / v_mu;
pi4(3)   = (2 * (m_lambda^2) * (1 + (2 * v_gamma))) / v_mu^2;
pi4(4)   = (4 * (m_lambda^3) * (v_gamma^2)) / v_mu^3;
pi4(5)   = ((m_lambda^4) * (v_gamma^4)) / v_mu^4;

rho_mc(4) = ((pi4/sum(pi4)) * [0:nodes4]')/nodes4;


fprintf("N=%d lamb=%4.1f mu=%3.1f gamma=%4.2f", nodes4, m_lambda, v_mu, v_gamma)
%fprintf("N=%d",nodes4)
for ch = 1:length(pi4)
    fprintf("\t \\tilde{\\pi_%d}=%.3f",ch, pi4(ch))
end
fprintf("\n")

fprintf("Results comparing Program and Markov Chain\n");
fprintf("nodes \t \\rho MC\t \\rho prog\n");
for i = 1:4
    fprintf("%d   \t %5.3f\t %5.3f\n", i, rho_mc(i), rho109b(i));
end

%% Verifing the growing
% figure
% num_aprox = ((rho109b) .* (([1:length(rho109b)] - ones(1,length(rho109b)))/2) );
% 
% plot(index/factor_int,'b-' , 'DisplayName', 'd*', 'LineWidth',2);
% hold on;
% %plot(expinf ./ 2 ,'r-x', 'DisplayName', '\rho(N) \times N/2');
% %hold on;
% %plot(expinf      ,'g-.', 'DisplayName', '\rho(N) \times N', 'LineWidth',2);
% %hold on;
% plot(num_aprox   ,'y--', 'DisplayName', '\rho(N) \times d', 'LineWidth',2);
% 
% lgd2 = legend('FontSize',7,'Location','southeast', 'Orientation','vertical');
% if lang == 1
%     xlabel('Number of vulnerable nodes');
%     ylabel('N*');
% else
%     xlabel('Número de nós vulneráveis');
%     ylabel('N*');
% end
% dim = [0.15 0.5 0.3 0.3];
% 
% 
% %txt1 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times N \\right]^2 = %0.2f$'     ,sum((index - (expinf)).^2) );
% %disp(txt1)
% %txt2 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times (N-1) \\right]^2 =  %0.2f$',sum((index - (num_aprox)).^2) );
% %disp(txt2)
% 
% %str = sprintf('%s\n%s', txt1, txt2);
% %annotation('textbox',dim,'String',str,'FitBoxToText','on', 'interpreter','latex');
% 
% str_file_pdf = sprintf('aproximacao_d_star_e_valor_esperado');
% if save_file
%     fig = gcf;
%     if fig_pdf == 0
%         str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.png');
%         fig.PaperUnits = 'centimeters';
%         fig.PaperPosition = [0 0 8.4 6.4];
%         print(fig,str_file_std,'-dpng','-r300');
%     else
%         str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
%         %fig.PaperPositionMode = 'auto';
%         fig.PaperUnits = 'centimeters';
%         fig.PaperPosition = [0 0 8.4 6.4];
%         fig_pos = fig.PaperPosition;
%         fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
%         print (fig,str_file_std,'-dpdf');
%     end
% end