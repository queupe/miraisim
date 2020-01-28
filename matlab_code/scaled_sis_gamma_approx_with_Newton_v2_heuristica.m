%% Scaled SIS infected model
% Simulates infected model from \gamma and \lambda
% Version 5:
% from version 3 created in class with Daniel, and
% changed:
% N - elements generations
% raised N until T
% include steps in N, gamma and lambda
% plot tagged node
% the second part, use Newton approximation

save_file = true;

OUTPUT_FOLDER_PDF = '../Notes/approx_Claude/img/';


%% Plotting for all
f = figure('visible','on');
hold on
xlabel('number of susceptible nodes');
ylabel('infection probability');
title('exact value and approximated with 2 iterations');

colored = [ [0, 0.4470, 0.7410], 
            [0.8500, 0.3250, 0.0980],
            [0.9290, 0.6940, 0.1250],
            [0.4940, 0.1840, 0.5560],
            [0.4660, 0.6740, 0.1880],
            [0.3010, 0.7450, 0.9330],
            [0.6350, 0.0780, 0.1840]
          ];

%% Real calculates, using the formulate exact

%  N - represents the total elements (individuals)
N       = 20;
qtd_N   = 15;
inf_N   = 8;
sup_N   = 59;
stp_N   = ceil((sup_N - inf_N)/qtd_N);
%vec_N = [1,2,3,4,5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 40, 44, 48, 52, 56, 60, 70, 80, 82, 84, 86, 88, 90, 100, 110];
vec_N = 1:3:110;
qtd_N = length(vec_N);

% Gamma represents the endogenous infection rate
% \gamma to be tested:
qtd_gamma = 3;
inf_gamma = 0.1;
sup_gamma = 3;
stp_gamma = ceil((sup_gamma - inf_gamma)/qtd_gamma)/2;
vec_gamma = [1.03, 1.06, 1.07, 1.08, 1.09, 1.15, 1.52];
%vec_gamma = [1.03];
%vec_gamma = [1.06];
%vec_gamma = [1.09];
%vec_gamma = [1.15];
qtd_gamma = length(vec_gamma);

% Lambda represents the exogenous infection rate
qtd_lambda = 100;
inf_lambda = 0.1;
sup_lambda = 10;
stp_lambda = ceil((sup_lambda - inf_lambda)/qtd_lambda);
vec_lambda = [10.0];
qtd_lambda = length(vec_lambda);

% healing rate
mu=1;

ilamda = 0;




%% Calculates all \tilde{\pi} - exact values
for sup_lambda = vec_lambda
	ilamda = ilamda +1;

	% Initializing \gamma index
	igamma=0;
	for gamma=vec_gamma
	    igamma=igamma+1;

	    % Inicializing N index
	    iN=0;

	    % For diferent N values
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
        plot(vec_N,pitaggedinfected,'Color',colored(1+mod(igamma, length(colored)),:),'DisplayName',sprintf('Exact \\gamma=%0.2f',gamma));
        hold on
        
	end
	% saveas(fig, sprintf('scaled_sis_gamma_lambda_is_%f.png',sup_lambda))
	%legend('show');
    xlim([0 90])
	%hold off

end

%% Newton approximation

T          = 400;
N          = 1:T;
gamma1_vec = vec_gamma;
mu1        = 1.0;
lambda1    = 10;

rho0 = zeros(length(gamma1_vec),T);
rho1 = zeros(length(gamma1_vec),T);
rhoS = zeros(length(gamma1_vec),T);

last_rho0 = 0;
last_rho1 = 1;

last_n_rho0 = 0;
last_n_rho1 = 0;

ylim([0, 1]);
xlim([1,T+70]);
igamma = 0;
for gamma1 = gamma1_vec
    igamma = igamma +1;
    for n = N
        rho0(igamma, n) = rho_zero_2iter(lambda1/n, mu1, gamma1, n-1);
        rho1(igamma, n) = rho_one_2iter (lambda1/n, mu1, gamma1, n-1);
        
    
        
        if n < 4
            if rho0(igamma, n) > 0 && rho0(igamma, n) < 1
                last_rho0 = rho0(igamma, n);
                last_n_rho0 = n;
            end
            if rho1(igamma, n) > 0 && rho1(igamma, n) < 1
                last_rho1 = rho1(igamma, n);
                last_n_rho1 = n;
            end          
        else
            if rho0(igamma, n) > 0 && rho0(igamma, n) < 1 && (rho0(igamma, n-2) - rho0(igamma, n-1)) > (rho0(igamma, n-1) - rho0(igamma, n)) 
                last_rho0 = rho0(igamma, n);
                last_n_rho0 = n;
            elseif rho0(igamma, n) > 0 && rho0(igamma, n) < 1
                last_rho0 = rho0(igamma, last_n_rho0-1) - (rho0(igamma, last_n_rho0-2) - rho0(igamma, last_n_rho0-1));
            end
            if rho1(igamma, n) > 0 && rho1(igamma, n) < 1 && (rho1(igamma, n-2) - rho1(igamma, n-1)) > (rho1(igamma, n-1) - rho1(igamma, n)) 
                last_rho1 = rho1(igamma, n);
                last_n_rho1 = n;
            elseif rho1(igamma, n) > 0 && rho1(igamma, n) < 1
                last_rho1 = rho1(igamma, last_n_rho0-1) - (rho1(igamma, last_n_rho1-2) - rho1(igamma, last_n_rho1-1));
            end
        end
        
        rhoS (igamma, n) = (last_rho0 + last_rho1)/2;
    end

    for n =  N(2:length(N))
        txt = sprintf('gamma=%0.2f; rho0(%3d)=%0.6f; rho1(%3d)=%0.6f; rhoS(%3d)=%0.6f; rho0(%3d)-rho0(%3d)=%0.6f; rho1(%3d)-rho1(%3d)=%0.6f', gamma1, n, rho0(igamma,n), n, rho1(igamma,n), n, rhoS(igamma,n), n-1, n, rho0(igamma,n-1) - rho0(igamma,n), n-1, n, rho1(igamma,n-1) - rho1(igamma,n));
        disp(txt);
    end

    plot(N(1:T), rho0(igamma,1:T),'--','Color',colored(1+mod(igamma, length(colored)),:), 'DisplayName', sprintf('\\gamma=%0.2f and \\rho_0=0', gamma1));
    hold on


end
igamma = 0;
for gamma1 = gamma1_vec
    igamma = igamma +1;
    
    plot(N(1:T), rho1(igamma,1:T),':','Color',colored(1+mod(igamma, length(colored)),:), 'LineWidth', 2, 'DisplayName', sprintf('\\gamma=%0.2f and \\rho_0=1', gamma1));
    hold on
end


igamma = 0;
for gamma1 = gamma1_vec
    igamma = igamma +1;
    
    plot(N(1:T), rhoS(igamma,1:T),'-.','Color',colored(1+mod(igamma, length(colored)),:), 'LineWidth', 2, 'DisplayName', sprintf('\\gamma=%0.2f and \\rho suavised', gamma1));
    hold on
end

lgd = legend('FontSize',7,'Location','southeast', 'Orientation','vertical','AutoUpdate','off');
grid();
%plot(N(1:T),0.6 .* ones(1,T), 'r')

str_file_pdf = sprintf('exact_approx_lambda%0.2f_gamma%0.2f_iter_%d', lambda1, gamma1, 2);

if save_file
    str_file_std = strcat(OUTPUT_FOLDER_PDF , strrep(str_file_pdf,'.','_'), '.pdf');
    %disp(str_file_std)
    fig = gcf;
    fig.PaperPositionMode = 'auto';
    fig_pos = fig.PaperPosition;
    fig.PaperSize = [fig_pos(3) fig_pos(4)];
    print (fig,str_file_std,'-dpdf');
end