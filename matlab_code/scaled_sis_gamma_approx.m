%% Scaled SIS infected model
% Simulates infected model from \gamma and \lambda
% Version 4:
% from version 3 created in class with Daniel, and
% changed:
% N - elements generations
% raised N until 30
% include steps in N, gamma and lambda
% plot tagged node

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';

%% Mean of infected

%  N - represents the total elements (individuals)
N=20;
qtd_N = 15;
inf_N = 8;
sup_N = 59;
stp_N = ceil((sup_N - inf_N)/qtd_N);
% vec_N = inf_N:stp_N:sup_N;
vec_N = [1,2,3,4,5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 40, 44, 48, 52, 56, 60, 70, 80, 90, 100, 110, 120];
qtd_N = length(vec_N);

% Gamma represents the endogenous infection rate
% \gamma to be tested:
qtd_gamma = 3;
inf_gamma = 0.1;
sup_gamma = 3;
stp_gamma = ceil((sup_gamma - inf_gamma)/qtd_gamma)/2;
%gamma_vec = inf_gamma:stp_gamma:sup_gamma;
%gamma_vec = [0.51 0.92 1.002 1.02 1.03 1.05 1.07 1.09 1.21 2.01];
%vec_gamma = [0.51 0.92 1.002 1.02 1.03 1.05 1.07 1.09 1.21 2.01];
vec_gamma = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
qtd_gamma = length(vec_gamma);

% Lambda represents the exogenous infection rate
qtd_lambda = 100;
inf_lambda = 0.1;
sup_lambda = 10;
stp_lambda = ceil((sup_lambda - inf_lambda)/qtd_lambda);
%vec_lambda = inf_lambda:stp_lambda:sup_lambda;
vec_lambda = [10.0];
qtd_lambda = length(vec_lambda);

% healing rate
mu=1;

ilamda = 0;
%% Plotting
fig = figure;
hold on
xlabel('number of nodes in the network');
ylabel('probability of tagged node is infected');

for sup_lambda = vec_lambda
	ilamda = ilamda +1;

	% Initializing \gamma index
	igamma=0;
	for gamma=vec_gamma
	    igamma=igamma+1;

	    % Inicializing N index
	    iN=0;

	    %% For diferent N values
	    for N=vec_N %% ((sup_lambda-inf_lambda)/qtd_lambda):sup_lambda
			iN=iN+1;
			% Define lambda (exogenous infection) in function of N
	        lambda = sup_lambda/N;
	        % Connectivity Matrix to completed graph
	        A=ones(N,N);
	        for i=1:N
	            A(i,i)=0;
	        end
	        % x is a vector representing the states, x(j) is the j-esimo element.
	        x=zeros(N,1);

	        % \pi is a vector representing the constant of equilibrium of
	        % transition states matrix Q and the probability of the states
	        % Initializing \pi
	        pi=zeros(N+1,1);
	        pi_ninf = zeros(1,N+1);
	        pi_tagged_inf = zeros(1,N+1);

	        % To contamitations 0..N
	        for i=0:N
	            % Load x to all states of contamination [0 0 ... 0]' until
	            % [1 1 ... 1]'
	            x=zeros(N,1);
	            for j=1:i
	                x(j)=1;
	            end

	            % To connetivity A:
	            % my_exponent1 is number of contamined edges
	            my_exponent1=((x'*A*x)/2);
	            pi(i+1) = (lambda/mu)^i * gamma^my_exponent1;
	            % differents arrangment of i contamined nodes
	            pi_ninf(i+1)=(nchoosek(N,i+1-1))*pi(i+1);

	            if (i>0)
	                % probability of a tagged node being infected
	                pi_tagged_inf(i+1)=(nchoosek(N-1,i+1-1-1))*pi(i+1);
	            else
	                % probability of a tagged node being infected is zero
	                pi_tagged_inf(i+1)=0; % pi(i+1);
	            end

	        end
	        spi{igamma,iN}.gamma=gamma;
	        spi{igamma,iN}.lambda=lambda;
	        spi{igamma,iN}.pi=pi;
	        spi{igamma,iN}.pi_ninf=pi_ninf;
	        spi{igamma,iN}.pi_tagged_inf=pi_tagged_inf;
	        spi{igamma,iN}.N=N;
	    end
	end




	igamma=0;
	% for all gamma
	for gamma=vec_gamma
		igamma=igamma+1;
	    iN=0;
	    meaninfected=zeros(qtd_N,1);
	    pitaggedinfected=zeros(qtd_N,1);
        
	    % for all N
	    for N=vec_N %
	        iN=iN+1;
	        pi=spi{igamma,iN}.pi_ninf;
	        meaninfected(iN)=(pi/sum(pi))*[0:1:N]';

	        pi_tagged=spi{igamma,iN}.pi_tagged_inf;
	        pitaggedinfected(iN)=sum(pi_tagged)/sum(pi);
            rho(iN) = ((sup_lambda/iN)*(gamma^(N/2))) / ( 1 + ((sup_lambda/iN)*(gamma^(N/2))));
        end
        plot(vec_N,pitaggedinfected,'DisplayName',sprintf('Exact \\gamma=%f',gamma));
        hold on
        
        %aproximação
        rN = [1:80];
        rho = zeros(length(rN),1);
        
        ri = 0;
        for rn = rN
            ri = ri+1;
            rho(ri) = ((sup_lambda/rn)*(gamma^(rn/2))) / ( 1 + ((sup_lambda/rn)*(gamma^(rn/2))));
            %fprintf('rho(%d) = %f\n',rn,rho(ri))
        end
        plot(rN,rho,'--','DisplayName',sprintf('Aprx N^{*} \\gamma=%f',gamma));
        hold on

		%plot(vec_N,meaninfected,'DisplayName',sprintf('\\gamma=%f',gamma));

	    %M = [inf_N:stp_N:sup_N; pitaggedinfected];

	    % csvwrite(sprintf('gamma_%f',gamma),pitaggedinfected);

	    % hold on
	end
	% saveas(fig, sprintf('scaled_sis_gamma_lambda_is_%f.png',sup_lambda))
	%legend('show');
    xlim([0 90])
	%hold off

end

grid();
lgd = legend('FontSize',8,'Location','southeast', 'Orientation','vertical','AutoUpdate','off');


str_file_pdf = sprintf('approx_N_lambda%0.2f_gamma%0.2f', lambda(1), gamma);

if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [fig_pos(3) fig_pos(4)];
    print (fig,str_file_std,'-dpdf');
end
