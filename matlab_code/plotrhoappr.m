clear all
syms cgamma n 


% Language: 0 - defaut (portuguese); 1 - English
lang = 0;

vec_elem = 1:100;
save_file = true;
OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';


rho=((10/n)*(cgamma^(n/2)))/(1+(10/n)*(cgamma^(n/2)));
rho109=eval(subs(rho,{n,cgamma},{vec_elem,1.09}));
hold on;
if lang == 1
    text_lang_001 = '\rho(n) when N^{*}=N/2';
else
    text_lang_001 = '\rho(n) quando N^{*}=N/2';
end
plot(rho109,'-', 'DisplayName', text_lang_001);

rho2t=((10/n)*(cgamma^(n)))/(1+(10/n)*(cgamma^(n)));
rho1092t=eval(subs(rho2t,{n,cgamma},{vec_elem,1.09}));
hold on;
if lang == 1
    text_lang = '\rho(n) when N^{*}=N';
else
    text_lang = '\rho(n) quando N^{*}=N';
end
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
	
    currho = zeros(1,2*nusers);
    for napp=1:2*nusers
		currho(napp)=((10/nusers)*(cgamma^(napp/2)))/(1+(10/nusers)*(cgamma^(napp/2)));
	end
	% approxatexp(nusers)=currho(max(floor(expinf(nusers)-2),1));
	[c, index(nusers)] = min(abs(currho-rho109b(nusers)));
	rho109approx(nusers)=currho(index(nusers));
end

if lang == 1
    text_lang = '\rho(n) exact';
else
    text_lang = '\rho(n) exato';
end
plot(rho109b, 'DisplayName', text_lang);

if lang == 1
    text_lang = '\rho(n) best approx.';
else
    text_lang = '\rho(n) melhor aprox.';
end
plot(rho109approx,'*', 'DisplayName', text_lang);
lgd = legend('FontSize',10,'Location','southeast', 'Orientation','vertical');
if lang == 1
    xlabel('Number of nodes in the network');
    ylabel('Prob. of susceptible node is infected (\rho)');
else
    xlabel('Número de nós na rede');
    ylabel('Prob. de um nó suscetível estar infectado (\rho)');
end
% plot(approxatexp,'+');
hold off

str_file_pdf = sprintf('aproximacao_n_star');
if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
    print (fig,str_file_std,'-dpdf');
end

figure
num_aprox = ((rho109b) .* ([1:length(rho109b)] - ones(1,length(rho109b))) );

plot(index       ,'b-' , 'DisplayName', 'N^{*}', 'LineWidth',2);
hold on;
plot(expinf      ,'r-x', 'DisplayName', '\rho(n) \times N/2');
hold on;
plot((2.*expinf) ,'g-.', 'DisplayName', '\rho(n) \times N', 'LineWidth',2);
hold on;
plot(num_aprox   ,'y--', 'DisplayName', '\rho(n) \times (N - 1)', 'LineWidth',2);

lgd2 = legend('FontSize',10,'Location','southeast', 'Orientation','vertical');
if lang == 1
    xlabel('Number of expected nodes infected');
    ylabel('Number of nodes in the network');
else
    ylabel('Número de nós infectados esperado');
    xlabel('Número de nós na rede');
end
dim = [0.15 0.5 0.3 0.3];


txt1 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times N \\right]^2 = %0.2f$'     ,sum((index - (2.*expinf)).^2) );
disp(txt1)
txt2 = sprintf('$\\sum\\limits_{n=1}^{N} \\left[N^{*}(n) - \\rho(n) \\times (N-1) \\right]^2 =  %0.2f$',sum((index - (num_aprox)).^2) );
disp(txt2)

str = sprintf('%s\n%s', txt1, txt2);
annotation('textbox',dim,'String',str,'FitBoxToText','on', 'interpreter','latex');

str_file_pdf = sprintf('aproximacao_n_star_e_valor_esperado');
if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [(fig_pos(3)+0.3), (fig_pos(4)+0.3)];
    print (fig,str_file_std,'-dpdf');
end