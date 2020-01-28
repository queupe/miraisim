function rho_end = scaledSISExact_allTopologies(vec_lambda, vec_mu, vec_gamma, vec_N, f_connection)


    %% Real calculates, using the formulate exact
    % Lambda represents the exogenous infection factor
    qtd_lambda  = length(vec_lambda);
    % healing factor
    qtd_mu      = length(vec_mu);
    % Gamma represents the endogenous infection factor
    qtd_gamma   = length(vec_gamma);
    %  N - represents the total susceptibles (individuals)
    qtd_N       = length(vec_N);
    
    rho = -1 * ones(qtd_lambda, qtd_mu, qtd_gamma, qtd_N);
    
    %% Calculates all \tilde{\pi} - exact values
    ilambda = 0;
    for sup_lambda = vec_lambda
        ilambda = ilambda +1;

        imu = 0;
        for mu = vec_mu
            imu = imu + 1;

            % Initializing \gamma index
            igamma=0;
            for gamma = vec_gamma
                igamma=igamma+1;
                %disp("Valor de gamma:")
                %disp(gamma)

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
                        for j=1:N
                            if i == j
                                A(i,i)=0;
                            else
                                A(i,j)=f_connection(i,j);
                            end
                            
                        end
                    end
                    % x is a vector representing the states, x(j) is the j-esimo element.
                    % x=zeros(N,1);

                    % \pi is a vector representing the constant of equilibrium of
                    % transition states matrix Q and the probability of the states
                    % Initializing \pi
                    pi            = zeros(N+1,1);
                    pi_ninf       = zeros(1,N+1);
                    pi_tagged_inf = zeros(1,N+1);

                   
                    % To contamitations 0..N
                    for i=0:N
                        
                        if (i>0)
                            C = nchoosek(1:N,i);
                            nc = size(C,1);
                            allperm = accumarray([repmat((1:nc)',i,1),C(:)],1);
                            fprintf("nc=%d",nc)
                            for j=1:nc
                                x = allperm(j,:);
                                % To connetivity A:
                                % my_exponent1 is number of contamined edges
                                my_exponent1=((x'*A*x)/2);

                                pi(i+1) = pi(i+1) + (lambda/mu)^i * gamma^my_exponent1;
                                % differents arrangment of i contamined nodes
                                pi_ninf(i+1)=(nchoosek(N,i+1-1))*pi(i+1);
                            end
                        

                            % probability of a tagged node being infected
                            pi_tagged_inf(i+1)= (nchoosek(N-1,i-1))*pi(i+1);
                        else
                            % probability of a tagged node being infected is zero
                            pi_tagged_inf(i+1)= 0; % pi(i+1);
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
                    %rho(iN) = ((sup_lambda/iN)*(gamma^(N/2))) / ( 1 + ((sup_lambda/iN)*(gamma^(N/2))));
                
                    rho(ilambda, imu, igamma, iN) = pitaggedinfected(iN);
                end


            end
        end % vec_mu
    end % vec_lambda
    
    rho_end = rho;

end