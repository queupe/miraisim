%% Scaled SIS infected model
% Simulates infected model from \gamma and \lambda
% Version 4:
% from version 3 created in class with Daniel, and
% changed:
% N - elements generations
% raised N until 30
% include steps in N, gamma and lambda
% plot tagged node


%% Mean of infected

%  N - represents the total elements (individuals)
N=20;
qtd_N = 15;
inf_N = 8;
sup_N = 59;
stp_N = ceil((sup_N - inf_N)/qtd_N);
% vec_N = inf_N:stp_N:sup_N;
vec_N = [1,2,3,4,5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 36, 40, 44, 48, 52, 56];
qtd_N = length(vec_N);

% Gamma represents the endogenous infection rate
% \gamma to be tested:
qtd_gamma = 3;
inf_gamma = 0.1;
sup_gamma = 3;
stp_gamma = ceil((sup_gamma - inf_gamma)/qtd_gamma)/2;
%vec_gamma = [0.51 0.92 1.002 1.02 1.03 1.05 1.07 1.09 1.21 2.01];
vec_gamma = [1.07 1.09];
qtd_gamma = length(vec_gamma);

% Lambda represents the exogenous infection rate
qtd_lambda = 100;
inf_lambda = 0.1;
sup_lambda = 10;
stp_lambda = ceil((sup_lambda - inf_lambda)/qtd_lambda);
%vec_lambda = inf_lambda:stp_lambda:sup_lambda;
vec_lambda = [10.0, 15.0, 20.0];
qtd_lambda = length(vec_lambda);

% healing rate
mu=1;

ilamda = 0;
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

	%% Plotting
	fig = figure;
	hold on
    title(sprintf('\\Lambda=%f',sup_lambda));
	xlabel('nós na rede');
	%ylabel('probability of tagged node is infected');
    ylabel('valor de $N$*','Interpreter','latex');

	igamma=0;
	% for all gamma
	for gamma=vec_gamma
		igamma=igamma+1;
	    iN=0;
	    meaninfected=zeros(qtd_N,1);
	    pitaggedinfected=zeros(qtd_N,1);
        rho_fnd = zeros(qtd_N,1);
        N_fnd = zeros(qtd_N,1);
        error_vec = zeros(qtd_N,1);
        
	    % for all N
	    for N=vec_N %
	        iN=iN+1;
	        pi=spi{igamma,iN}.pi_ninf;
	        meaninfected(iN)=(pi/sum(pi))*[0:1:N]';

	        pi_tagged=spi{igamma,iN}.pi_tagged_inf;
	        pitaggedinfected(iN)=sum(pi_tagged)/sum(pi);
            rho_org = pitaggedinfected(iN);
            %rho(iN) = ((sup_lambda/iN)*(gamma^(n/2))) / ( 1 + ((sup_lambda/iN)*(gamma^(n/2))));
 
            %aproximação
            rN = [0:0.0001:30];
            N_apr_sup = iN;
            N_apr_inf = iN;
            N_sup_best = iN;
            N_inf_best = iN;
            
            error = inf;
            rho_ast_sup = ((sup_lambda/iN)*(gamma^((iN-1)/2))) / ( 1 + ((sup_lambda/iN)*(gamma^((iN-1)/2))));
            rho_ast_inf = rho_ast_sup;
            
            sup = 0;
            rpt = 0;

            ri = 0;
            
            
            for rn = rN
                ri = ri+1;
                
                N_apr_sup = N_apr_sup + 0.0001;
                N_apr_inf = N_apr_inf - 0.0001;
                rho_ast_sup = ((sup_lambda/N_apr_sup)*(gamma^((N_apr_sup-1)/2))) / ( 1 + ((sup_lambda/N_apr_sup)*(gamma^((N_apr_sup-1)/2))));
                rho_ast_inf = ((sup_lambda/N_apr_inf)*(gamma^((N_apr_inf-1)/2))) / ( 1 + ((sup_lambda/N_apr_inf)*(gamma^((N_apr_inf-1)/2))));
                
                if (abs(rho_ast_sup - rho_org) < abs(rho_ast_inf - rho_org))
                    if rpt < 3
                        rpt = rpt +1;
                    else
                        sup = 1;
                    end
                else
                    rpt = 0;
                end
                
                if sup == 0
                    if abs(rho_ast_inf - rho_org) < error
                        error = abs(rho_ast_inf - rho_org );
                        rho_fnd(iN) = rho_ast_inf;
                        error_vec(iN) = error;
                        N_fnd(iN) = N_apr_inf;                    
                    end
                else
                    if abs(rho_ast_sup - rho_org ) < error
                        error = abs(rho_ast_sup - rho_org );
                        rho_fnd(iN) = rho_ast_sup;
                        error_vec(iN) = error;
                        N_fnd(iN) = N_apr_sup;
                    end
                end
                
            end
            fprintf('Lambda=%f ; gamma=%f ; N=%f; N*=%f; rho:%f ; rho^:%f; error=%f\n',sup_lambda, gamma, vec_N(iN), N_fnd(iN) , rho_org, rho_fnd(iN), error)
        
        end
        
        %plot(vec_N, rho,'-x' , 'DisplayName', sprintf('\\rho^ \\gamma=%f',gamma))
        %plot(vec_N, pitaggedinfected,'--' , 'DisplayName', sprintf('\\rho \\gamma=%f',gamma))
        plot(vec_N,N_fnd, 'DisplayName', sprintf('\\gamma=%f',gamma))

        %plot(vec_N,pitaggedinfected,'DisplayName',sprintf('\\gamma=%f',gamma));
        %plot(rN,rho_ast,'--')
		%plot(vec_N,meaninfected,'DisplayName',sprintf('\\gamma=%f',gamma));

	    %M = [inf_N:stp_N:sup_N; pitaggedinfected];

	    % csvwrite(sprintf('gamma_%f',gamma),pitaggedinfected);

	    % hold on
	end
	% saveas(fig, sprintf('scaled_sis_gamma_lambda_is_%f.png',sup_lambda))
	legend('show');
    xlim([0 90])
	hold off

end
