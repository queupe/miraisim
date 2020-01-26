clear all
syms cgamma n 


% Language: 0 - defaut (portuguese); 1 - English
lang = 0;

% Figure to presentation -> 0; to paper -> 1
fig_pdf = 1; 

vec_elem = 1:100;
save_file = true;
%OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';
OUTPUT_FOLDER_PDF = '/home/vilc/Dropbox/UFRJ/followavoidcrowd/epssis/paper/epidemic_model_approx/edition/model/';


rho=((10/n)*(cgamma^(n/2)))/(1+(10/n)*(cgamma^(n/2)));
rho109=eval(subs(rho,{n,cgamma},{vec_elem,1.09}));
hold on;
if lang == 1
    text_lang_001 = '\rho(n) when N^{*}=N/2';
else
    text_lang_001 = '\rho(n) quando N^{*}=N/2';
end
% closed form N*=N/2
plot(rho109,'-', 'DisplayName', text_lang_001);

rho2t=((10/n)*(cgamma^(n)))/(1+(10/n)*(cgamma^(n)));
rho1092t=eval(subs(rho2t,{n,cgamma},{vec_elem,1.09}));
hold on;
if lang == 1
    text_lang = '\rho(n) when N^{*}=N';
else
    text_lang = '\rho(n) quando N^{*}=N';
end
% closed form N*=N
plot(rho1092t,'.-', 'DisplayName', text_lang);

%rho2v=((10/n)*(cgamma^(n-1)))/(1+(10/n)*(cgamma^(n-1)));
%rho1092v=eval(subs(rho2v,{n,cgamma},{vec_elem,1.09}));
%hold on;
%plot(rho1092v,'.-', 'DisplayName', 'N^{*}=N-1');

index        = zeros(1,length(vec_elem));
rho109approx = zeros(1,length(vec_elem));

cgamma=1.09;
for nusers=vec_elem
    
	zsum   = 0;
	expsum = 0;
	
    for i=0:nusers
		curzsum=nchoosek(nusers,i)*((10/nusers)^i)*cgamma^(i*(i-1)/2);
		expsum=expsum+i*curzsum;
		zsum=zsum+curzsum;
    end
    
	rho109b(nusers) = (1/nusers)*(expsum/zsum);
	expinf(nusers)  = (expsum/zsum);
	clear currho;
	
    currho = zeros(1,nusers);
    for napp=1:nusers
		currho(napp)=((10/nusers)*(cgamma^(napp)))/(1+(10/nusers)*(cgamma^(napp)));
	end
	% approxatexp(nusers)=currho(max(floor(expinf(nusers)-2),1));
	[c, index(nusers)] = min(abs(currho-rho109b(nusers)));
	rho109approx(nusers)=currho(index(nusers));
end

if lang == 1
    text_lang = '\rho(n)';
else
    text_lang = '\rho(n)';
end
% calculated from formulation
plot(rho109b, 'DisplayName', text_lang);

if lang == 1
    text_lang = '\rho(N) optimal N*';
else
    text_lang = '\rho(N) melhor aprox.';
end
% get the best n*
plot(rho109approx,'*', 'DisplayName', text_lang);
lgd = legend('FontSize',7,'Location','southeast', 'Orientation','vertical');
if lang == 1
    xlabel('Number of vulnerable nodes');
    ylabel('Infection probability');
else
    xlabel('Número de nós vulneráveis');
    ylabel('Probabilidade de Infecção');
end
% plot(approxatexp,'+');
hold off

str_file_pdf = sprintf('aproximacao_n_star');
if save_file
    %disp(str_file_std)
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

figure
num_aprox = ((rho109b) .* ([1:length(rho109b)] - ones(1,length(rho109b))) );

plot(index       ,'b-' , 'DisplayName', 'N^{*}', 'LineWidth',2);
hold on;
%plot(expinf ./ 2 ,'r-x', 'DisplayName', '\rho(N) \times N/2');
%hold on;
%plot(expinf      ,'g-.', 'DisplayName', '\rho(N) \times N', 'LineWidth',2);
%hold on;
plot(num_aprox   ,'y--', 'DisplayName', '\rho(N) \times (N - 1)', 'LineWidth',2);

lgd2 = legend('FontSize',7,'Location','southeast', 'Orientation','vertical');
if lang == 1
    xlabel('Number of vulnerable nodes');
    ylabel('N*');
else
    xlabel('Número de nós vulneráveis');
    ylabel('N*');
end
dim = [0.15 0.5 0.3 0.3];


txt1 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times N \\right]^2 = %0.2f$'     ,sum((index - (expinf)).^2) );
disp(txt1)
txt2 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times (N-1) \\right]^2 =  %0.2f$',sum((index - (num_aprox)).^2) );
disp(txt2)

%str = sprintf('%s\n%s', txt1, txt2);
%annotation('textbox',dim,'String',str,'FitBoxToText','on', 'interpreter','latex');

str_file_pdf = sprintf('aproximacao_n_star_e_valor_esperado');
if save_file
    
    %disp(str_file_std)
    fig = gcf;
    if fig_pdf == 0
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.png');
        %fig.PaperUnits = 'inches';
        %fig.PaperPosition = [0 0 6 3];
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        print(fig,str_file_std,'-dpng','-r300');
    else
        str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
        %fig.PaperPositionMode = 'auto';
        fig.PaperUnits = 'centimeters';
        fig.PaperPosition = [0 0 8.4 6.4];
        fig_pos = fig.PaperPosition;
        fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
        print (fig,str_file_std,'-dpdf');
    end
end