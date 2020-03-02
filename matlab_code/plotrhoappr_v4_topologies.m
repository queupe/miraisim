clear all
close all
syms cgamma n d

global NumUsu;

v_lambda = 10;
v_mu     = 1;
v_gamma  = 2.39;


% Bipartite form: 0 - full bipartite; 1 - degree ciclic bipartite
bip_form = 0;

if bip_form == 0
    % full bipartite
    degree_vec = [0/1, 2/2, 4/3, 8/4, 12/5, 18/6, 24/7, 32/8];
    f = @connection_bipartite_knm;
    file_name = 'aproximacao_n_star_bipartite';

elseif bip_form == 1
    degree_vec = [0/1, 2/2, 4/3, 8/4, 12/5, 18/6, 18/7, 24/8];
    f = @connection_bipartite_d;
    file_name = 'aproximacao_n_star_ciclic_avg_deg';

end

% Language: 0 - defaut (portuguese); 1 - English
lang = 1;

if lang == 1
    text_lang_001 = '\rho(n), d*=d/2';
    text_lang_002 = '\rho(n)';
    text_lang_003 = '\rho(n)';
    text_lang_004 = '\rho(n), optimal d*';
    text_lang_005 = 'Number of vulnerable nodes';
    text_lang_006 = 'Infection probability';
    text_lang_007 = 'd*';
elseif lang == 0
    text_lang_001 = '\rho(n), d*=d/2';
    text_lang_002 = '\rho(n)';
    text_lang_003 = '\rho(n)';
    text_lang_004 = '\rho(n), d* ótimo';
    text_lang_005 = 'Número de nós vulneráveis';
    text_lang_006 = 'Probabilidade de Infecção0';
    text_lang_007 = 'd*';
end

    

% Figure to presentation -> 0; to paper -> 1
fig_pdf = 1; 

tot_user = 8;
vec_elem = 1:tot_user;

save_file = true;
%OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';
%OUTPUT_FOLDER_PDF = '/home/vilc/Dropbox/UFRJ/followavoidcrowd/epssis/paper/epidemic_model_approx/edition/model/';
OUTPUT_FOLDER_PDF = '/home/vilc/Documents/UFRJ/git/mirai_graph/rhoappr/';


%% closed form d*=d/2 (d -> degree)
rho=((v_lambda/(n*v_mu))*(cgamma^(d/2)))/(1+(v_lambda/(n*v_mu))*(cgamma^(d/2)));
rho109_binom=eval(subs(rho,{n,cgamma,d},{vec_elem,v_gamma,degree_vec})); 

hold on;
plot(rho109_binom,'-', 'Color', [0 0.4470 0.7410], 'DisplayName', text_lang_001, 'LineWidth', 1.5);

%% closed form d*=d (d -> degree)
rho2t   = ((v_lambda/(n*v_mu))*(cgamma^(d)))/(1+(v_lambda/(n*v_mu))*(cgamma^(d)));
rho1092t_binom=eval(subs(rho2t,{n,cgamma,d},{vec_elem,v_gamma,degree_vec}));

hold on;
plot(rho1092t_binom,'-', 'Color', [0.000 0.510 0.000],'DisplayName', text_lang_002, 'LineWidth', 1.5);

%% Exact value

fprintf("Partial results on program\n");
rho109b_aux = scaledSISExact_allTopologies_v2(v_lambda, v_mu, v_gamma, vec_elem, f);
rho109_exact = squeeze(rho109b_aux(1,1,1,:));
rho109_exact = rho109_exact';

hold on;
plot(rho109_exact, 'Color', [0.9290 0.6940 0.1250], 'DisplayName', text_lang_003', 'LineWidth', 1.5);

%% Best approximation
index_approx  = zeros(1,length(vec_elem));
rho109_approx = zeros(1,length(vec_elem));
d_star_approx = zeros(1,length(vec_elem));

for nusers=vec_elem
	clear currho;
	factor_int = 8;
    currho    = zeros(1,factor_int*nusers +1);
    curd_star = zeros(1,factor_int*nusers +1); 
    for dege_app=0:1/factor_int:nusers
		currho(factor_int*dege_app+1)=((v_lambda/(nusers*v_mu))*(v_gamma^(dege_app)))/(1+((v_lambda/(nusers*v_mu))*(v_gamma^(dege_app))));
        curd_star(factor_int*dege_app+1)=dege_app;
    end

	[c, index_approx(nusers)] = min(abs(currho-rho109_exact(nusers)));
	rho109_approx(nusers)     = currho(index_approx(nusers));
    d_star_approx(nusers)     = curd_star(index_approx(nusers));
end

hold on;
plot(rho109_approx,'LineStyle', 'none', 'DisplayName', text_lang_004, 'Marker', 'o', 'MarkerSize', 5.0, 'MarkerEdgeColor', [0.4940 0.1840 0.5560] ,  'LineWidth', 1.5);
hold on;

%% Closing plot
%lgd = legend('FontSize',10,'Location','southeast', 'Orientation','vertical');
xlabel(text_lang_005,'FontSize',14);
ylabel(text_lang_006,'FontSize',14);
grid minor;
%ylim([0.7,1])


%% Saving file
if save_file
    fig = gcf;
    if fig_pdf == 0
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(file_name,'.','_'), '.png');
        fig.PaperUnits = 'inches';
        fig.PaperPosition = [0 0 6 3];
        print(fig,str_file_std,'-dpng','-r300');
    else
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(file_name,'.','_'), '.pdf');
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        %fig.PaperPositionMode = 'auto';
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
end
hold off


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
    fprintf("%d   \t %5.3f\t %5.3f\n", i, rho_mc(i), rho109_exact(i));
end

%% Verifing the growing
figure
num_aprox = (rho109_exact .* degree_vec);

plot(vec_elem, d_star_approx, 'LineStyle', 'none'   , 'DisplayName', 'N^{*}','Marker', 'o', 'MarkerSize', 5.0, 'MarkerEdgeColor', [0.4940 0.1840 0.5560], 'LineWidth',1.5);
hold on;
plot(vec_elem, num_aprox   ,'r-', 'DisplayName', '\rho(N) \times d', 'LineWidth',1.5);
hold on;

%lgd2 = legend('FontSize',7,'Location','southeast', 'Orientation','vertical');
grid minor;
xlabel(text_lang_005,'FontSize',14);
ylabel(text_lang_007,'FontSize',14);


dim = [0.15 0.5 0.3 0.3];
if save_file
    fig = gcf;
    if fig_pdf == 0
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(file_name,'.','_'), '_mean.png');
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        print(fig,str_file_std,'-dpng','-r300');
    else
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(file_name,'.','_'), '_mean.pdf');
        %fig.PaperPositionMode = 'auto';
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
end